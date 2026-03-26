"""
TEST MOBILE INFERENCE TREN 10 ANH
Dataset: D:\doc3d_dataset\extracted\image
"""

import numpy as np
import cv2
import onnxruntime as ort
import torch
import torch.nn.functional as F
import time
import os
from pathlib import Path

# Config
MODEL_PATH = 'model_mobile/docscanner.onnx'
INPUT_FOLDER = r'D:\doc3d_dataset\extracted\image'
OUTPUT_FOLDER = r'D:\doc3d_dataset\extracted\output_mobile'
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


class DocScannerONNX:
    def __init__(self, model_path):
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self.session = ort.InferenceSession(model_path, sess_options=sess_options, providers=['CPUExecutionProvider'])
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        self.input_size = self.session.get_inputs()[0].shape[2]
        print(f"[OK] Model loaded: {self.input_size}x{self.input_size}")

    def scan(self, image_bgr):
        """
        Giong inference.py: anh vao mang la RGB [0,1]; dau ra ONNX la luoi
        da chuan hoa cho grid_sample (khong duoc doi them cong thuc remap sai).
        """
        original_h, original_w = image_bgr.shape[:2]
        rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        im_ori = rgb.astype(np.float32) / 255.0

        im288 = cv2.resize(im_ori, (self.input_size, self.input_size))
        img = np.expand_dims(im288.transpose(2, 0, 1), axis=0).astype(np.float32)

        bm = self.session.run([self.output_name], {self.input_name: img})[0]

        bm0 = cv2.resize(bm[0, 0], (original_w, original_h))
        bm1 = cv2.resize(bm[0, 1], (original_w, original_h))
        bm0 = cv2.blur(bm0, (3, 3))
        bm1 = cv2.blur(bm1, (3, 3))
        lbl = np.stack([bm0, bm1], axis=2)

        with torch.no_grad():
            t_in = torch.from_numpy(im_ori).permute(2, 0, 1).unsqueeze(0).float()
            t_grid = torch.from_numpy(lbl).unsqueeze(0).float()
            out = F.grid_sample(t_in, t_grid, align_corners=True)

        result_rgb = (out[0].permute(1, 2, 0).numpy().clip(0, 1) * 255).astype(np.uint8)
        return cv2.cvtColor(result_rgb, cv2.COLOR_RGB2BGR)


def main():
    print("=" * 60)
    print("TEST MOBILE INFERENCE - 10 ANH")
    print("=" * 60)

    # Load model
    print(f"\n[1] Loading model...")
    scanner = DocScannerONNX(MODEL_PATH)

    # Get 10 images
    print(f"\n[2] Lay 10 anh tu: {INPUT_FOLDER}")
    all_files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith(('.jpg', '.png', '.jpeg'))]
    test_files = all_files[:10]

    if len(test_files) == 0:
        print("[LOI] Khong tim thay anh nao!")
        return

    print(f"    Tim thay {len(all_files)} anh, test {len(test_files)} anh")

    # Process each image
    print(f"\n[3] Xu ly {len(test_files)} anh...")
    print("-" * 60)

    results = []
    for i, fname in enumerate(test_files):
        input_path = os.path.join(INPUT_FOLDER, fname)
        output_path = os.path.join(OUTPUT_FOLDER, fname.replace('.jpg', '_mobile.png').replace('.jpeg', '_mobile.png'))

        # Read
        image = cv2.imread(input_path)
        if image is None:
            print(f"[{i+1:2d}/10] LOI doc anh: {fname}")
            results.append({'file': fname, 'status': 'read_error', 'time': 0})
            continue

        h, w = image.shape[:2]
        print(f"[{i+1:2d}/10] {fname} | {w}x{h}", end=" | ")

        # Inference
        start = time.time()
        result = scanner.scan(image)
        elapsed = time.time() - start

        # Save
        cv2.imwrite(output_path, result)

        print(f"{elapsed*1000:.0f}ms | {result.shape[1]}x{result.shape[0]} | [OK]")
        results.append({'file': fname, 'status': 'ok', 'time': elapsed * 1000, 'size': image.shape})

    # Summary
    print("-" * 60)
    print(f"\n[4] KET QUA:")
    print(f"    Da xu ly: {len([r for r in results if r['status']=='ok'])}/{len(test_files)} anh")

    ok_times = [r['time'] for r in results if r['status'] == 'ok']
    if ok_times:
        avg = sum(ok_times) / len(ok_times)
        min_t = min(ok_times)
        max_t = max(ok_times)
        print(f"    Thoi gian TB: {avg:.0f}ms")
        print(f"    Nhanh nhat: {min_t:.0f}ms")
        print(f"    Cham nhat: {max_t:.0f}ms")
        print(f"    FPS: {1000/avg:.1f}")

    print(f"\n[5] Luu ket qua vao:")
    print(f"    {OUTPUT_FOLDER}")

    # Show first result
    print("\n[6] Xem ket qua truoc:")
    first_ok = next((r for r in results if r['status'] == 'ok'), None)
    if first_ok:
        out_path = os.path.join(OUTPUT_FOLDER, first_ok['file'].replace('.jpg', '_mobile.png').replace('.jpeg', '_mobile.png'))
        print(f"    {out_path}")


if __name__ == "__main__":
    main()
