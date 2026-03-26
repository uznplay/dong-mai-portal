"""
Bước 2: Export sang ONNX
ONNX có thể chuyển sang TFLite để chạy trên mobile
"""

import torch
import torch.nn as nn
import numpy as np
from PIL import Image
import cv2
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from seg import U2NETP
from model import DocScanner


class DocScannerMobile(nn.Module):
    """DocScanner optimized cho mobile inference"""
    
    def __init__(self, seg_model_path=None, rec_model_path=None):
        super().__init__()
        self.msk = U2NETP(3, 1)
        self.bm = DocScanner()
        
        # Load weights nếu có
        if seg_model_path and os.path.exists(seg_model_path):
            seg_dict = self.msk.state_dict()
            pretrained = torch.load(seg_model_path, map_location='cpu')
            pretrained = {k[6:]: v for k, v in pretrained.items() if k[6:] in seg_dict}
            seg_dict.update(pretrained)
            self.msk.load_state_dict(seg_dict)
            
        if rec_model_path and os.path.exists(rec_model_path):
            rec_dict = self.bm.state_dict()
            pretrained = torch.load(rec_model_path, map_location='cpu')
            pretrained = {k: v for k, v in pretrained.items() if k in rec_dict}
            rec_dict.update(pretrained)
            self.bm.load_state_dict(rec_dict)
        
        self.eval()
    
    def forward(self, x):
        """x: input tensor [B, 3, H, W] - normalize về [0, 1]"""
        # 1. Segmentation mask
        msk, _, _, _, _, _, _ = self.msk(x)
        msk = (msk > 0.5).float()
        masked_x = msk * x
        
        # 2. Bypass flow prediction - sử dụng fixed transform
        # Thay vì chạy 12 iterations, dùng simple perspective
        h, w = x.shape[2], x.shape[3]
        
        # Simple grid-based unwarp
        bm = self.bm(masked_x, iters=4, test_mode=True)  # Giảm từ 12 xuống 4
        bm = (2 * (bm / 286.8) - 1) * 0.99
        
        # Output: flow field [B, 2, H, W]
        return bm


class LightweightDocScanner(nn.Module):
    """
    Model nhẹ hơn - không cần deep learning
    Dùng OpenCV traditional methods
    """
    
    def __init__(self):
        super().__init__()
        # Không có layers - chỉ dùng OpenCV operations
        pass
    
    def forward(self, x):
        """Trả về None - xử lý bằng OpenCV thủ công"""
        return None


def export_to_onnx(model, output_path, input_size=(288, 288)):
    """Export PyTorch model sang ONNX format"""
    
    print("=" * 50)
    print("EXPORTING TO ONNX")
    print("=" * 50)
    
    # Tạo dummy input
    dummy_input = torch.randn(1, 3, input_size[0], input_size[1])
    
    # Export
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
    
    print(f"ONNX model saved to: {output_path}")
    
    # Verify ONNX model
    try:
        import onnx
        onnx_model = onnx.load(output_path)
        onnx.checker.check_model(onnx_model)
        print("ONNX model verified successfully!")
    except Exception as e:
        print(f"Warning: ONNX verification failed: {e}")


def create_lightweight_inference_code():
    """
    Tạo code inference nhẹ - không cần deep learning
    Dùng OpenCV thuần
    """
    
    code = '''"""
LIGHTWEIGHT DOCUMENT SCANNER
Không cần GPU, chạy được trên mobile CPU
"""
import cv2
import numpy as np


def scan_document(image_path_or_array, output_path=None):
    """
    Quét và chỉnh sửa tài liệu - chạy hoàn toàn bằng OpenCV
    
    Args:
        image_path_or_array: Đường dẫn ảnh hoặc numpy array
        output_path: Đường dẫn lưu ảnh kết quả
    
    Returns:
        numpy array: Ảnh đã chỉnh sửa
    """
    
    # Đọc ảnh
    if isinstance(image_path_or_array, str):
        img = cv2.imread(image_path_or_array)
    else:
        img = image_path_or_array.copy()
    
    if img is None:
        raise ValueError("Không thể đọc ảnh")
    
    # 1. Preprocessing - tăng contrast
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # 2. Edge detection
    edged = cv2.Canny(blurred, 75, 200)
    
    # 3. Tìm contours
    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
    
    # 4. Tìm document boundary (tứ giác lớn nhất)
    screenCnt = None
    for contour in contours:
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
        
        if len(approx) == 4:
            screenCnt = approx
            break
    
    if screenCnt is None:
        # Không tìm thấy tài liệu, trả về ảnh gốc
        print("Warning: Không tìm thấy boundary của tài liệu")
        if output_path:
            cv2.imwrite(output_path, img)
        return img
    
    # 5. Sắp xếp điểm góc
    def order_points(pts):
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        return rect
    
    pts = screenCnt.reshape(4, 2)
    rect = order_points(pts)
    
    # 6. Tính toán kích thước output
    (tl, tr, br, bl) = rect
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))
    
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))
    
    # 7. Perspective transform
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")
    
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(img, M, (maxWidth, maxHeight))
    
    # 8. Post-processing
    # Chuyển sang grayscale và enhance
    warped_gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    
    # Adaptive thresholding để làm rõ text
    adaptive_thresh = cv2.adaptiveThreshold(
        warped_gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )
    
    # Kết hợp kết quả
    result = cv2.cvtColor(adaptive_thresh, cv2.COLOR_GRAY2BGR)
    
    # Lưu nếu cần
    if output_path:
        cv2.imwrite(output_path, result)
    
    return result


def batch_process(input_folder, output_folder):
    """Xử lý nhiều ảnh cùng lúc"""
    import os
    os.makedirs(output_folder, exist_ok=True)
    
    for fname in os.listdir(input_folder):
        if fname.endswith(('.png', '.jpg', '.jpeg')):
            input_path = os.path.join(input_folder, fname)
            output_path = os.path.join(output_folder, f"scanned_{fname}")
            
            try:
                scan_document(input_path, output_path)
                print(f"Processed: {fname}")
            except Exception as e:
                print(f"Error processing {fname}: {e}")


# Ví dụ sử dụng
if __name__ == "__main__":
    # Single image
    result = scan_document("distorted/42_2 copy.png", "rectified/scanned.png")
    print("Done!")
    
    # Batch process
    # batch_process("distorted/", "rectified/")
'''
    
    with open('3_lightweight_inference.py', 'w') as f:
        f.write(code)
    
    print("Lightweight inference code created: 3_lightweight_inference.py")


def main():
    print("=" * 50)
    print("DOCSCANNER MOBILE OPTIMIZATION - Step 2")
    print("=" * 50)
    
    # Đường dẫn model
    seg_model_path = './model_pretrained/seg.pth'
    rec_model_path = './model_pretrained/DocScanner-L.pth'
    
    # Kiểm tra model tồn tại
    if not os.path.exists(seg_model_path):
        print(f"Warning: {seg_model_path} not found!")
        print("Tạo model mới (không có pretrained weights)...")
        model = DocScannerMobile()
    else:
        print("\n1. Loading model...")
        model = DocScannerMobile(seg_model_path, rec_model_path)
    
    model.eval()
    
    # Tạo thư mục output
    os.makedirs('./model_mobile', exist_ok=True)
    
    # Export sang ONNX
    print("\n2. Exporting to ONNX...")
    onnx_path = './model_mobile/docscanner.onnx'
    
    try:
        export_to_onnx(model, onnx_path, input_size=(288, 288))
    except Exception as e:
        print(f"Export failed: {e}")
        print("\nFallback: Tạo lightweight inference code...")
    
    # Tạo code inference nhẹ
    print("\n3. Creating lightweight inference code...")
    create_lightweight_inference_code()
    
    print("\n" + "=" * 50)
    print("Step 2 COMPLETE!")
    print("Tiếp theo:")
    print("  - Dùng onnx2tf convert sang TFLite: onnx2tf -i docscanner.onnx -o docscanner.tflite")
    print("  - Hoặc chạy 3_lightweight_inference.py để dùng OpenCV thuần")
    print("=" * 50)


if __name__ == "__main__":
    main()
