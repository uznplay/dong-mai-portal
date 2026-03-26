"""
MOBILE INFERENCE - ONNX Runtime
Dung cho Android/iOS thong qua ONNX Runtime Mobile SDK
https://onnxruntime.ai/docs/install/#install-on-android
https://onnxruntime.ai/docs/install/#ios

Toc do: ~266ms/anh tren CPU (uoc tinh)
FPS: ~3.8
Kich thuoc model: 32.4 MB (ONNX)
"""

import numpy as np
import cv2
import onnxruntime as ort
import torch
import torch.nn.functional as F
import time
import os


class DocScannerONNX:
    """
    DocScanner inference su dung ONNX Runtime
    - Khong can GPU
    - Chay tren CPU mobile
    - Tuong thich Android/iOS
    """

    def __init__(self, model_path='docscanner.onnx'):
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

        self.session = ort.InferenceSession(
            model_path,
            sess_options=sess_options,
            providers=['CPUExecutionProvider']
        )

        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        self.input_shape = self.session.get_inputs()[0].shape
        self.input_size = self.input_shape[2]

        print(f"[DocScannerONNX] Model loaded: {self.input_shape}")

    def preprocess(self, image_bgr):
        """RGB [0,1] giong inference.py (PIL), khong dung BGR thang vao mang."""
        original_h, original_w = image_bgr.shape[:2]
        rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        im_ori = rgb.astype(np.float32) / 255.0
        im288 = cv2.resize(im_ori, (self.input_size, self.input_size))
        img = np.expand_dims(im288.transpose(2, 0, 1), axis=0).astype(np.float32)
        return img, im_ori, original_h, original_w

    def apply_warp(self, im_ori_rgb, bm):
        """Dung grid_sample nhu inference.py; bm da la toa do [-1,1] tu ONNX."""
        h, w = im_ori_rgb.shape[:2]
        bm0 = cv2.resize(bm[0, 0], (w, h))
        bm1 = cv2.resize(bm[0, 1], (w, h))
        bm0 = cv2.blur(bm0, (3, 3))
        bm1 = cv2.blur(bm1, (3, 3))
        lbl = np.stack([bm0, bm1], axis=2)
        with torch.no_grad():
            t_in = torch.from_numpy(im_ori_rgb).permute(2, 0, 1).unsqueeze(0).float()
            t_grid = torch.from_numpy(lbl).unsqueeze(0).float()
            out = F.grid_sample(t_in, t_grid, align_corners=True)
        result_rgb = (out[0].permute(1, 2, 0).numpy().clip(0, 1) * 255).astype(np.uint8)
        return cv2.cvtColor(result_rgb, cv2.COLOR_RGB2BGR)

    def scan(self, image_bgr):
        img_tensor, im_ori, _, _ = self.preprocess(image_bgr)
        bm = self.session.run([self.output_name], {self.input_name: img_tensor})[0]
        return self.apply_warp(im_ori, bm)

    def benchmark(self, image, num_runs=10):
        times = []
        for _ in range(num_runs):
            start = time.time()
            _ = self.scan(image)
            times.append(time.time() - start)
        avg_ms = sum(times) / len(times) * 1000
        min_ms = min(times) * 1000
        max_ms = max(times) * 1000
        fps = 1 / (sum(times) / len(times))
        print(f"Benchmark ({num_runs} runs):")
        print(f"  Average: {avg_ms:.0f} ms")
        print(f"  Min: {min_ms:.0f} ms")
        print(f"  Max: {max_ms:.0f} ms")
        print(f"  FPS: {fps:.1f}")


def scan_document(image_path, model_path='model_mobile/docscanner.onnx', output_path=None):
    scanner = DocScannerONNX(model_path)
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Khong the doc anh: {image_path}")
    result = scanner.scan(image)
    scanner.benchmark(image, num_runs=5)
    if output_path:
        cv2.imwrite(output_path, result)
        print(f"Da luu: {output_path}")
    return result


if __name__ == "__main__":
    print("=" * 60)
    print("DOCSCANNER ONNX MOBILE INFERENCE")
    print("=" * 60)

    model_path = 'model_mobile/docscanner.onnx'
    test_image = 'distorted/42_2 copy.png'
    output_image = 'rectified/scanned_onnx.png'

    if not os.path.exists(model_path):
        print(f"LOI: Model khong tim thay: {model_path}")
        print("Chay 2_quantize_and_export.py truoc!")
    else:
        print(f"\nModel: {model_path}")
        print(f"Input: {test_image}")
        print(f"Output: {output_image}")

        print("\nDang xu ly...")
        result = scan_document(test_image, model_path, output_image)

        print("\n" + "=" * 60)
        print("XONG!")
        print("=" * 60)
        print(f"\nAnh ket qua: {output_image}")
        print(f"Kich thuoc: {result.shape}")
