"""
LIGHTWEIGHT DOCUMENT SCANNER
Không cần GPU, chạy được trên mobile CPU
Dùng OpenCV thuần - tốc độ nhanh, kích thước nhỏ
"""

import cv2
import numpy as np
import os


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
    
    original_h, original_w = img.shape[:2]
    
    # 1. Preprocessing - tăng contrast và giảm noise
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
        # Không tìm thấy tài liệu, trả về ảnh gốc đã enhance
        print("Warning: Không tìm thấy boundary của tài liệu, trả về ảnh enhanced")
        # Thử blur nhẹ thay vì full
        result = cv2.bilateralFilter(img, 9, 75, 75)
        if output_path:
            cv2.imwrite(output_path, result)
        return result
    
    # 5. Sắp xếp điểm góc (top-left, top-right, bottom-right, bottom-left)
    def order_points(pts):
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]  # top-left
        rect[2] = pts[np.argmax(s)]  # bottom-right
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]  # top-right
        rect[3] = pts[np.argmax(diff)]  # bottom-left
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
    
    # Đảm bảo kích thước hợp lệ
    maxWidth = max(maxWidth, 100)
    maxHeight = max(maxHeight, 100)
    
    # 7. Perspective transform
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")
    
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(img, M, (maxWidth, maxHeight))
    
    # 8. Post-processing - làm sạch và enhance
    # Chuyển sang grayscale
    warped_gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    
    # Adaptive thresholding để làm rõ text
    thresh = cv2.adaptiveThreshold(
        warped_gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )
    
    # Denoise nhẹ
    denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
    
    # Convert back to color
    result = cv2.cvtColor(denoised, cv2.COLOR_GRAY2BGR)
    
    # Lưu nếu cần
    if output_path:
        cv2.imwrite(output_path, result)
    
    return result


def scan_document_with_dewarp(image_path_or_array, output_path=None):
    """
    Phiên bản nâng cao - có thêm dewarp effect
    Mô phỏng một phần DocScanner deep learning bằng image processing
    """
    
    # Đọc ảnh
    if isinstance(image_path_or_array, str):
        img = cv2.imread(image_path_or_array)
    else:
        img = image_path_or_array.copy()
    
    # Apply document boundary detection và perspective transform
    result = scan_document(img)
    
    # Thêm một số enhancement
    # Tăng sharpness
    kernel = np.array([[-1,-1,-1], 
                       [-1, 9,-1],
                       [-1,-1,-1]])
    result = cv2.filter2D(result, -1, kernel)
    
    # Contrast adjustment
    lab = cv2.cvtColor(result, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l = cv2.equalizeHist(l)
    result = cv2.merge([l, a, b])
    result = cv2.cvtColor(result, cv2.COLOR_LAB2BGR)
    
    if output_path:
        cv2.imwrite(output_path, result)
    
    return result


def batch_process(input_folder, output_folder):
    """Xử lý nhiều ảnh cùng lúc"""
    os.makedirs(output_folder, exist_ok=True)
    
    for fname in os.listdir(input_folder):
        if fname.endswith(('.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG')):
            input_path = os.path.join(input_folder, fname)
            output_path = os.path.join(output_folder, f"scanned_{fname}")
            
            try:
                result = scan_document(input_path, output_path)
                print(f"[OK] Processed: {fname}")
            except Exception as e:
                print(f"[ERROR] {fname}: {e}")


def benchmark(image_path):
    """Đo tốc độ xử lý"""
    import time
    
    # Test nhiều lần để lấy trung bình
    times = []
    for i in range(5):
        start = time.time()
        result = scan_document(image_path)
        elapsed = time.time() - start
        times.append(elapsed)
    
    avg_time = sum(times) / len(times)
    print(f"\nBenchmark Results:")
    print(f"  Average time: {avg_time*1000:.1f} ms")
    print(f"  FPS: {1/avg_time:.1f}")
    print(f"  Min: {min(times)*1000:.1f} ms")
    print(f"  Max: {max(times)*1000:.1f} ms")


# Ví dụ sử dụng
if __name__ == "__main__":
    import sys
    
    # Lấy đường dẫn ảnh test
    test_image = "distorted/42_2 copy.png"
    output_image = "rectified/scanned_lightweight.png"
    
    if len(sys.argv) > 1:
        test_image = sys.argv[1]
    
    if len(sys.argv) > 2:
        output_image = sys.argv[2]
    
    print("=" * 50)
    print("LIGHTWEIGHT DOCUMENT SCANNER")
    print("=" * 50)
    print(f"Input: {test_image}")
    print(f"Output: {output_image}")
    print()
    
    # Benchmark
    benchmark(test_image)
    
    # Process
    print("\nProcessing...")
    result = scan_document(test_image, output_image)
    print(f"Done! Output saved to: {output_image}")
    
    # Batch process (uncomment nếu muốn)
    # print("\nBatch processing...")
    # batch_process("distorted/", "rectified/")
