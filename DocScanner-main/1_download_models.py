"""
Bước 1: Tải Pretrained Models
Chạy script này để tải model từ Google Drive
"""

import gdown
import os
import sys

def download_models():
    """Tải pretrained models từ Google Drive"""
    
    MODEL_DIR = './model_pretrained'
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    print("=" * 50)
    print("TẢI PRETRAINED MODELS")
    print("=" * 50)
    
    # Tải seg.pth
    seg_path = os.path.join(MODEL_DIR, 'seg.pth')
    if not os.path.exists(seg_path):
        print("\n[1/2] Dang tai seg.pth...")
        # Dùng direct URL format cho gdown
        url = "https://drive.google.com/uc?id=1mmCUj90rHyuO1SmpLt361youh-07Y0sD"
        try:
            gdown.download(url, seg_path, quiet=False)
            print("   [OK] seg.pth")
        except Exception as e:
            print(f"   [LOI] {e}")
            print("   Tai thu cong: https://drive.google.com/file/d/1mmCUj90rHyuO1SmpLt361youh-07Y0sD/view")
    else:
        sz = os.path.getsize(seg_path) / 1024 / 1024
        print(f"\n[1/2] seg.pth da ton tai ({sz:.1f} MB)")
    
    # Tải DocScanner-L.pth
    rec_path = os.path.join(MODEL_DIR, 'DocScanner-L.pth')
    if not os.path.exists(rec_path):
        print("\n[2/2] Dang tai DocScanner-L.pth...")
        # Thử folder link
        try:
            url = "https://drive.google.com/drive/folders/1W1_DJU8dfEh6FqDYqFQ7ypR38Z8c5r4D"
            gdown.download_folder(url, output_dir=MODEL_DIR, quiet=False)
            
            # Tim file trong folder
            for f in os.listdir(MODEL_DIR):
                if 'DocScanner' in f or 'docscanner' in f.lower():
                    if f.endswith('.pth'):
                        downloaded = os.path.join(MODEL_DIR, f)
                        if downloaded != rec_path:
                            os.rename(downloaded, rec_path)
                        print("   [OK] DocScanner-L.pth")
                        break
        except Exception as e:
            print(f"   [LOI] {e}")
            print("   Tai thu cong tu:")
            print("   https://drive.google.com/drive/folders/1W1_DJU8dfEh6FqDYqFQ7ypR38Z8c5r4D")
    else:
        sz = os.path.getsize(rec_path) / 1024 / 1024
        print(f"\n[2/2] DocScanner-L.pth da ton tai ({sz:.1f} MB)")
    
    # Kiem tra
    print("\n" + "=" * 50)
    print("KIEM TRA")
    print("=" * 50)
    for fname in ['seg.pth', 'DocScanner-L.pth']:
        fpath = os.path.join(MODEL_DIR, fname)
        if os.path.exists(fpath):
            sz = os.path.getsize(fpath) / 1024 / 1024
            print(f"  [OK] {fname}: {sz:.1f} MB")
        else:
            print(f"  [CHUA CO] {fname}")
    
    print("\nXong! Chay tiep 2_quantize_and_export.py")


if __name__ == "__main__":
    download_models()
