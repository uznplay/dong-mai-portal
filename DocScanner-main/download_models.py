"""
TẢI PRETRAINED MODELS TỪ GOOGLE DRIVE
"""

import gdown
import os
import sys

def download_models():
    """Tải pretrained models từ Google Drive"""
    
    MODEL_DIR = './model_pretrained'
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    # Google Drive links từ README
    models = {
        'seg.pth': 'https://drive.google.com/file/d/1mmCUj90rHyuO1SmpLt361youh-07Y0sD/view?usp=sharing',
        'DocScanner-L.pth': 'https://drive.google.com/drive/folders/1W1_DJU8dfEh6FqDYqFQ7ke5nu0Mpr4dW?usp=sharing'
    }
    
    print("=" * 50)
    print("TẢI PRETRAINED MODELS")
    print("=" * 50)
    
    # Tải seg.pth (đính kèm trong paper)
    seg_path = os.path.join(MODEL_DIR, 'seg.pth')
    if not os.path.exists(seg_path):
        print("\n1. Đang tải seg.pth...")
        try:
            gdown.download(models['seg.pth'], seg_path, fuzzy=True)
            print("   [OK] seg.pth")
        except Exception as e:
            print(f"   [LỖI] {e}")
            print("   Bạn cần tải thủ công từ Google Drive")
    else:
        print("\n1. seg.pth đã tồn tại")
    
    # Tải DocScanner-L.pth
    rec_path = os.path.join(MODEL_DIR, 'DocScanner-L.pth')
    if not os.path.exists(rec_path):
        print("\n2. Đang tải DocScanner-L.pth...")
        try:
            # Thử tải trực tiếp
            gdown.download_folder(
                'https://drive.google.com/drive/folders/1W1_DJU8dfEh6FqDYqFQ7ke5nu0Mpr4dW',
                output_dir=MODEL_DIR,
                quiet=False
            )
            
            # Đổi tên nếu cần
            for f in os.listdir(MODEL_DIR):
                if 'DocScanner' in f and f.endswith('.pth'):
                    os.rename(os.path.join(MODEL_DIR, f), rec_path)
            
            print("   [OK] DocScanner-L.pth")
        except Exception as e:
            print(f"   [LỖI] {e}")
            print("   Bạn cần tải thủ công từ Google Drive")
            print("   Link: https://drive.google.com/drive/folders/1W1_DJU8dfEh6FqDYqFQ7ke5nu0Mpr4dW")
    else:
        print("\n2. DocScanner-L.pth đã tồn tại")
    
    # Kiểm tra kết quả
    print("\n" + "=" * 50)
    print("KIỂM TRA MODEL")
    print("=" * 50)
    
    for fname in ['seg.pth', 'DocScanner-L.pth']:
        fpath = os.path.join(MODEL_DIR, fname)
        if os.path.exists(fpath):
            size_mb = os.path.getsize(fpath) / 1024 / 1024
            print(f"  [OK] {fname}: {size_mb:.1f} MB")
        else:
            print(f"  [CHƯA CÓ] {fname}")
    
    print("\nNếu model chưa tải được, hãy tải thủ công từ:")
    print("  - seg.pth: https://drive.google.com/file/d/1mmCUj90rHyuO1SmpLt361youh-07Y0sD/view")
    print("  - DocScanner-L.pth: https://drive.google.com/drive/folders/1W1_DJU8dfEh6FqDYqFQ7ke5nu0Mpr4dW")
    print("  Sau đó đặt vào thư mục model_pretrained/")


if __name__ == "__main__":
    try:
        import gdown
    except ImportError:
        print("Cài đặt gdown...")
        os.system("pip install gdown")
        import gdown
    
    download_models()
