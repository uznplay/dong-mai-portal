"""
Bước 1: Quantize Model PyTorch (FP32 -> INT8)
Giảm kích thước model ~4 lần, chạy được trên CPU mobile
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from PIL import Image
import os
import copy

# Import từ project gốc
from seg import U2NETP
from model import DocScanner


class QuantizedNet(nn.Module):
    """Model inference không cần GPU - chạy trên CPU mobile"""
    
    def __init__(self, seg_model_path, rec_model_path):
        super().__init__()
        self.msk = U2NETP(3, 1)
        self.bm = DocScanner()
        
        # Load weights
        if os.path.exists(seg_model_path):
            seg_dict = self.msk.state_dict()
            pretrained = torch.load(seg_model_path, map_location='cpu')
            pretrained = {k[6:]: v for k, v in pretrained.items() if k[6:] in seg_dict}
            seg_dict.update(pretrained)
            self.msk.load_state_dict(seg_dict)
            
        if os.path.exists(rec_model_path):
            rec_dict = self.bm.state_dict()
            pretrained = torch.load(rec_model_path, map_location='cpu')
            pretrained = {k: v for k, v in pretrained.items() if k in rec_dict}
            rec_dict.update(pretrained)
            self.bm.load_state_dict(rec_dict)
    
    def forward(self, x):
        # Segmentation mask
        msk, _, _, _, _, _, _ = self.msk(x)
        msk = (msk > 0.5).float()
        x = msk * x
        
        # Bypass iterative refinement - chạy nhanh hơn
        bm = self.bm(x, iters=12, test_mode=True)
        bm = (2 * (bm / 286.8) - 1) * 0.99
        
        return bm


def prepare_calibration_data(data_dir='./distorted', num_samples=10):
    """Chuẩn bị data để calibrate cho quantization"""
    images = []
    for i, fname in enumerate(os.listdir(data_dir)):
        if fname.endswith(('.png', '.jpg', '.jpeg')) and i < num_samples:
            img = np.array(Image.open(os.path.join(data_dir, fname)))[:, :, :3]
            img = img.astype(np.float32) / 255.0
            # Resize về 288x288
            import cv2
            img = cv2.resize(img, (288, 288))
            # CHW format
            img = img.transpose(2, 0, 1)
            images.append(img)
    
    if not images:
        # Tạo dummy data nếu không có ảnh
        images = [np.random.randn(3, 288, 288).astype(np.float32)]
    
    return images


class Quantizer:
    """Dynamic Quantization - không cần calibration data"""
    
    @staticmethod
    def dynamic_quantize(model):
        """Dynamic Quantization: chỉ quantize weights, activations vẫn float32"""
        quantized_model = copy.deepcopy(model)
        
        # Quantize weights của tất cả Conv2d và Linear layers
        for name, module in quantized_model.named_modules():
            if isinstance(module, (nn.Conv2d, nn.Linear)):
                # Dynamic quantization
                module.weight.data = module.weight.data.to(torch.qint8)
        
        return quantized_model
    
    @staticmethod
    def static_quantize(model, calibration_data):
        """Static Quantization: cần calibration data"""
        model.eval()
        
        # Fuse layers để tăng speed
        model_fused = copy.deepcopy(model)
        
        # Prepare model for static quantization
        model_fused.qconfig = torch.quantization.get_default_qconfig('fbgemm')
        torch.quantization.prepare(model_fused, inplace=True)
        
        # Calibrate với data
        with torch.no_grad():
            for i, img in enumerate(calibration_data[:5]):
                x = torch.from_numpy(img).float().unsqueeze(0)
                _ = model_fused(x)
        
        # Convert sang quantized model
        model_quantized = torch.quantization.convert(model_fused, inplace=False)
        
        return model_quantized


def save_quantized_model(model, save_path):
    """Lưu quantized model"""
    torch.save(model.state_dict(), save_path)
    print(f"Quantized model saved to: {save_path}")


def main():
    print("=" * 50)
    print("DOCSCANNER MOBILE OPTIMIZATION - Step 1")
    print("=" * 50)
    
    # Đường dẫn model
    seg_model_path = './model_pretrained/seg.pth'
    rec_model_path = './model_pretrained/DocScanner-L.pth'
    
    # Tạo model
    print("\n1. Loading original model...")
    model = QuantizedNet(seg_model_path, rec_model_path)
    model.eval()
    
    # Tính kích thước
    param_size = 0
    for param in model.parameters():
        param_size += param.nelement() * param.element_size()
    size_mb = param_size / 1024 / 1024
    print(f"   Original model size: {size_mb:.2f} MB")
    
    # Prepare calibration data
    print("\n2. Preparing calibration data...")
    cal_data = prepare_calibration_data()
    print(f"   Using {len(cal_data)} images for calibration")
    
    # Quantization
    print("\n3. Applying dynamic quantization...")
    quantized_model = Quantizer.dynamic_quantize(model)
    
    # Tính kích thước sau quantize
    param_size_q = 0
    for param in quantized_model.parameters():
        param_size_q += param.nelement() * param.element_size()
    size_mb_q = param_size_q / 1024 / 1024
    print(f"   Quantized model size: {size_mb_q:.2f} MB")
    print(f"   Size reduction: {size_mb / size_mb_q:.1f}x")
    
    # Lưu model
    print("\n4. Saving quantized model...")
    os.makedirs('./model_mobile', exist_ok=True)
    save_path = './model_mobile/docscanner_quant.pth'
    save_quantized_model(quantized_model, save_path)
    
    print("\n" + "=" * 50)
    print("Step 1 COMPLETE!")
    print("Tiếp theo: Chạy 2_export_onnx.py để export sang ONNX")
    print("=" * 50)


if __name__ == "__main__":
    main()
