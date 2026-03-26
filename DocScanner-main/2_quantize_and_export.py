"""
Bước 2: Quantize Model + Export Sang ONNX + TFLite
Chạy script này sau khi đã tải pretrained models
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from PIL import Image
import cv2
import os
import sys

print("=" * 60)
print("DOCSCANNER MOBILE OPTIMIZATION - Quantize & Export")
print("=" * 60)

# Import project modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from seg import U2NETP
from model import DocScanner


class DocScannerLite(nn.Module):
    """DocScanner optimized cho mobile - giảm iterations để nhanh hơn"""
    
    def __init__(self, seg_path, rec_path):
        super().__init__()
        
        # Segmentation model (U2NETP)
        self.msk = U2NETP(3, 1)
        if os.path.exists(seg_path):
            seg_dict = self.msk.state_dict()
            pretrained = torch.load(seg_path, map_location='cpu', weights_only=False)
            # Keys have "model." prefix
            pretrained = {k.replace('model.', ''): v for k, v in pretrained.items()}
            seg_dict.update({k: v for k, v in pretrained.items() if k in seg_dict})
            self.msk.load_state_dict(seg_dict)        
        # Rectification model (DocScanner)
        self.bm = DocScanner()
        if os.path.exists(rec_path):
            rec_dict = self.bm.state_dict()
            pretrained = torch.load(rec_path, map_location='cpu', weights_only=False)
            pretrained = {k: v for k, v in pretrained.items() if k in rec_dict}
            rec_dict.update(pretrained)
            self.bm.load_state_dict(rec_dict)
        
        self.eval()
    
    def forward(self, x):
        """Forward pass - x: [B, 3, 288, 288] normalized [0, 1]"""
        # 1. Segmentation mask
        msk, _, _, _, _, _, _ = self.msk(x)
        msk = (msk > 0.5).float()
        x = msk * x
        
        # 2. Rectification - giảm iterations từ 12 xuống 4 để nhanh
        bm = self.bm(x, iters=4, test_mode=True)
        bm = (2 * (bm / 286.8) - 1) * 0.99
        
        return bm


def load_and_preprocess_image(img_path, size=288):
    """Load và preprocess ảnh cho inference"""
    img = np.array(Image.open(img_path))[:, :, :3]
    img = img.astype(np.float32) / 255.0
    original_h, original_w = img.shape[:2]
    img = cv2.resize(img, (size, size))
    img = img.transpose(2, 0, 1)  # HWC -> CHW
    return torch.from_numpy(img).float().unsqueeze(0), original_h, original_w


def postprocess_output(bm, original_h, original_w):
    """Postprocess output từ model"""
    bm = bm.cpu()
    bm0 = cv2.resize(bm[0, 0].numpy(), (original_w, original_h))
    bm1 = cv2.resize(bm[0, 1].numpy(), (original_w, original_h))
    bm0 = cv2.blur(bm0, (3, 3))
    bm1 = cv2.blur(bm1, (3, 3))
    lbl = torch.from_numpy(np.stack([bm0, bm1], axis=2)).unsqueeze(0)
    return lbl


def quantize_model_pt(model):
    """Quantize PyTorch model sang INT8"""
    print("\n[2.1] Quantizing PyTorch model...")
    
    # Dynamic quantization - quantize weights sang int8
    quantized_model = torch.quantization.quantize_dynamic(
        model, 
        {nn.Conv2d, nn.Linear}, 
        dtype=torch.qint8
    )
    
    # Tính size
    orig_size = sum(p.nelement() * p.element_size() for p in model.parameters()) / 1024 / 1024
    quant_size = sum(p.nelement() * p.element_size() for p in quantized_model.parameters()) / 1024 / 1024
    
    print(f"   Original: {orig_size:.1f} MB")
    print(f"   Quantized: {quant_size:.1f} MB")
    print(f"   Reduction: {orig_size/quant_size:.1f}x")
    
    return quantized_model


def export_to_onnx(model, output_path, input_size=288):
    """Export model sang ONNX"""
    print(f"\n[2.2] Exporting to ONNX...")
    
    model.eval()
    dummy_input = torch.randn(1, 3, input_size, input_size)
    
    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        export_params=True,
        opset_version=11,
        do_constant_folding=True,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={
            'input': {0: 'batch_size', 2: 'height', 3: 'width'},
            'output': {0: 'batch_size', 2: 'height', 3: 'width'}
        }
    )
    
    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"   ONNX saved: {output_path} ({size_mb:.1f} MB)")
    
    return output_path


def convert_tflite(onnx_path, output_path):
    """Convert ONNX sang TFLite"""
    print(f"\n[2.3] Converting ONNX to TFLite...")
    
    try:
        # Thử dùng onnx2tf
        os.system(f'onnx2tf -i "{onnx_path}" -o "{output_path}" -oao')
        if os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / 1024 / 1024
            print(f"   TFLite saved: {output_path} ({size_mb:.1f} MB)")
            return True
    except:
        pass
    
    # Fallback: dùng onnxruntime + tf
    try:
        import onnx
        from onnx import shape_inference
        import tensorflow as tf
        
        # Load and optimize ONNX
        onnx_model = onnx.load(onnx_path)
        
        # Convert sang TF
        from onnx_tf.backend import prepare
        tf_rep = prepare(onnx_model)
        
        # Export TF model
        tf_model_path = output_path.replace('.tflite', '_tf')
        tf_rep.export_graph(tf_model_path)
        
        # Convert sang TFLite
        converter = tf.lite.TFLiteConverter.from_saved_model(tf_model_path)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        converter.target_spec.supported_types = [tf.float16]
        tflite_model = converter.convert()
        
        with open(output_path, 'wb') as f:
            f.write(tflite_model)
        
        size_mb = os.path.getsize(output_path) / 1024 / 1024
        print(f"   TFLite saved: {output_path} ({size_mb:.1f} MB)")
        return True
    except Exception as e:
        print(f"   [WARN] TFLite conversion failed: {e}")
        print("   Bạn có thể convert thủ công bằng:")
        print("   1. onnx2tf -i docscanner.onnx -o docscanner.tflite")
        print("   2. Hoặc dùng https://convertmodel.com/")
        return False


def test_inference(model, image_path):
    """Test inference với ảnh"""
    print(f"\n[2.4] Testing inference...")
    
    import time
    
    # Load ảnh
    img_tensor, h, w = load_and_preprocess_image(image_path)
    
    # Test nhiều lần
    times = []
    for i in range(3):
        start = time.time()
        with torch.no_grad():
            bm = model(img_tensor)
        elapsed = time.time() - start
        times.append(elapsed)
    
    avg_time = sum(times) / len(times)
    print(f"   Average inference time: {avg_time*1000:.0f} ms")
    print(f"   FPS: {1/avg_time:.1f}")
    
    return avg_time


def main():
    # Đường dẫn
    seg_path = './model_pretrained/seg.pth'
    rec_path = './model_pretrained/DocScanner-L.pth'
    output_dir = './model_mobile'
    os.makedirs(output_dir, exist_ok=True)
    
    # Kiểm tra model tồn tại
    print("\n[1] Checking pretrained models...")
    for name, path in [('Segmentation', seg_path), ('Rectification', rec_path)]:
        if os.path.exists(path):
            sz = os.path.getsize(path) / 1024 / 1024
            print(f"   [OK] {name}: {sz:.1f} MB")
        else:
            print(f"   [MISSING] {name}: {path}")
            print("   Chạy 1_download_models.py trước!")
            return
    
    # Load model
    print("\n[2] Loading model...")
    model = DocScannerLite(seg_path, rec_path)
    print("   [OK] Model loaded")
    
    # Tính size
    param_size = sum(p.nelement() * p.element_size() for p in model.parameters()) / 1024 / 1024
    print(f"   Model size: {param_size:.1f} MB")
    
    # Test inference
    test_image = './distorted/42_2 copy.png'
    if os.path.exists(test_image):
        test_inference(model, test_image)
    
    # Quantize
    print("\n[3] Quantizing model...")
    quantized_model = quantize_model_pt(model)
    
    # Lưu quantized model
    quant_path = os.path.join(output_dir, 'docscanner_quant.pth')
    torch.save(quantized_model.state_dict(), quant_path)
    print(f"   [OK] Saved: {quant_path}")
    
    # Export ONNX
    print("\n[4] Exporting to ONNX...")
    onnx_path = os.path.join(output_dir, 'docscanner.onnx')
    export_to_onnx(quantized_model, onnx_path, input_size=288)
    
    # Convert TFLite
    print("\n[5] Converting to TFLite...")
    tflite_path = os.path.join(output_dir, 'docscanner.tflite')
    
    # Thử onnx2tf trực tiếp
    print("   Running: onnx2tf -i docscanner.onnx -o docscanner.tflite")
    result = os.system(f'onnx2tf -i "{onnx_path}" -o "{tflite_path}" -oao 2>&1')
    
    if result == 0 and os.path.exists(tflite_path):
        sz = os.path.getsize(tflite_path) / 1024 / 1024
        print(f"   [OK] TFLite: {sz:.1f} MB")
    else:
        print("   [INFO] TFLite conversion cần thêm bước:")
        print("   Run: onnx2tf -i model_mobile/docscanner.onnx -o model_mobile/docscanner.tflite")
    
    # Tạo inference code
    print("\n[6] Creating mobile inference code...")
    
    inference_code = '''"""
TFLite Inference Code cho Mobile
Copy file này vào project mobile của bạn
"""

import numpy as np
import cv2
import tensorflow as tf


class DocScannerTFLite:
    """DocScanner inference using TFLite"""
    
    def __init__(self, model_path):
        self.interpreter = tf.lite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        
        self.input_shape = self.input_details[0]['shape']
        self.input_size = self.input_shape[1]  # 288
        
        print(f"Model loaded: {self.input_shape}")
    
    def preprocess(self, image):
        """Preprocess ảnh"""
        # Resize
        original_h, original_w = image.shape[:2]
        img = cv2.resize(image, (self.input_size, self.input_size))
        
        # Normalize [0, 1]
        img = img.astype(np.float32) / 255.0
        
        # HWC -> CHW
        img = img.transpose(2, 0, 1)
        
        # Add batch dim
        img = np.expand_dims(img, axis=0)
        
        return img.astype(np.float32), original_h, original_w
    
    def postprocess(self, bm, original_h, original_w):
        """Postprocess output"""
        bm = bm[0]  # Remove batch dim
        
        # Resize flow field
        bm0 = cv2.resize(bm[:, :, 0], (original_w, original_h))
        bm1 = cv2.resize(bm[:, :, 1], (original_w, original_h))
        
        # Blur
        bm0 = cv2.blur(bm0, (3, 3))
        bm1 = cv2.blur(bm1, (3, 3))
        
        return bm0, bm1
    
    def scan(self, image):
        """Scan document"""
        img_tensor, original_h, original_w = self.preprocess(image)
        
        # Run inference
        self.interpreter.set_tensor(self.input_details[0]['index'], img_tensor)
        self.interpreter.invoke()
        
        # Get output
        bm = self.interpreter.get_tensor(self.output_details[0]['index'])
        
        # Postprocess
        bm0, bm1 = self.postprocess(bm, original_h, original_w)
        
        return bm0, bm1


def scan_document(image_path, model_path='docscanner.tflite', output_path=None):
    """Quét document đơn giản"""
    
    # Load model
    scanner = DocScannerTFLite(model_path)
    
    # Read image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Cannot read image")
    
    # Scan
    bm0, bm1 = scanner.scan(image)
    
    print(f"Flow field computed: {bm0.shape}")
    print("Done!")
    
    # Lưu flow field nếu cần
    if output_path:
        flow = np.stack([bm0, bm1], axis=-1)
        np.save(output_path.replace('.png', '_flow.npy'), flow)
    
    return bm0, bm1


# Test
if __name__ == "__main__":
    import time
    
    # Test với ảnh
    scanner = DocScannerTFLite('model_mobile/docscanner.tflite')
    
    image = cv2.imread('distorted/42_2 copy.png')
    
    start = time.time()
    bm0, bm1 = scanner.scan(image)
    elapsed = time.time() - start
    
    print(f"Inference time: {elapsed*1000:.0f} ms")
'''
    
    with open('model_mobile/tflite_inference.py', 'w', encoding='utf-8') as f:
        f.write(inference_code)
    print("   [OK] Created: model_mobile/tflite_inference.py")
    
    print("\n" + "=" * 60)
    print("HOAN TAT!")
    print("=" * 60)
    print("\nModel files:")
    for f in os.listdir(output_dir):
        sz = os.path.getsize(os.path.join(output_dir, f)) / 1024 / 1024
        print(f"  - {f}: {sz:.1f} MB")
    print("\nSu dung TFLite model trong app mobile của bạn!")


if __name__ == "__main__":
    main()
