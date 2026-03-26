"""
Export docscanner.onnx cho browser inference (ONNX Runtime Web).
Chiến lược: Dùng WASM backend (không phải WebGL) vì:
  - grid_sampler cần opset 16 (WebGL k hỗ trợ opset 16 cho Split)
  - WASM backend hỗ trợ ceil_mode=True (MaxPool)
"""
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import torch
import torch.nn as nn
import numpy as np

from seg import U2NETP
from model import DocScanner


def _load_seg_into_msk(msk: nn.Module, seg_path: str) -> None:
    """Giong inference.py / 2_export_onnx: seg.pth thuong co prefix 6 ky tu."""
    if not seg_path or not os.path.exists(seg_path):
        print(f"[WARN] Khong tim thay {seg_path} — U2NETP de mac dinh (ONNX se sai segmentation!)")
        return
    seg_dict = msk.state_dict()
    pretrained = torch.load(seg_path, map_location="cpu", weights_only=False)
    stripped = {k[6:]: v for k, v in pretrained.items() if k[6:] in seg_dict}
    if len(stripped) >= max(8, len(seg_dict) // 4):
        seg_dict.update(stripped)
        used = len(stripped)
    else:
        direct = {k: v for k, v in pretrained.items() if k in seg_dict}
        seg_dict.update(direct)
        used = len(direct)
    msk.load_state_dict(seg_dict)
    print(f"  Da load seg: {seg_path} ({used} tensors)")


class DocScannerLite(nn.Module):
    """DocScanner cho browser inference — seg.pth + DocScanner-L.pth."""

    def __init__(self, rec_path, seg_path=None):
        super().__init__()
        self.msk = U2NETP(3, 1)
        self.bm = DocScanner()

        seg_default = os.path.join("model_pretrained", "seg.pth")
        _load_seg_into_msk(self.msk, seg_path or seg_default)

        if os.path.exists(rec_path):
            print(f"Loading rectification weights from: {rec_path}")
            rec_dict = self.bm.state_dict()
            pretrained = torch.load(rec_path, map_location='cpu', weights_only=False)

            loaded = 0
            for k, v in pretrained.items():
                if k in rec_dict:
                    rec_dict[k] = v
                    loaded += 1
            self.bm.load_state_dict(rec_dict)
            print(f"  Da load {loaded}/{len(rec_dict)} rectification weights")
        else:
            print(f"[WARN] Khong tim thay {rec_path} — dung random weights")

        self.eval()

    def forward(self, x):
        msk, _, _, _, _, _, _ = self.msk(x)
        msk = (msk > 0.5).float()
        x = msk * x
        bm = self.bm(x, iters=4, test_mode=True)
        bm = (2 * (bm / 286.8) - 1) * 0.99
        return bm


if __name__ == '__main__':
    rec_path = 'model_pretrained/DocScanner-L.pth'
    seg_path = os.path.join('model_pretrained', 'seg.pth')
    output = 'model_mobile/docscanner.onnx'

    print("=" * 50)
    print("EXPORTING DOCSCANNER ONNX (WASM-compatible)")
    print("=" * 50)
    print("  Backend:  WASM (khong dung WebGL)")
    print("  opset:    16 (grid_sampler requires)")
    print("  iters:    4")
    print("  seg:     ", seg_path)
    print("=" * 50)

    model = DocScannerLite(rec_path, seg_path=seg_path)
    model.eval()

    dummy = torch.randn(1, 3, 288, 288)

    print("\nExporting to ONNX (opset=16)...")
    torch.onnx.export(
        model, dummy, output,
        export_params=True,
        opset_version=16,
        do_constant_folding=True,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={
            'input': {0: 'batch_size', 2: 'height', 3: 'width'},
            'output': {0: 'batch_size', 2: 'height', 3: 'width'}
        }
    )

    size_mb = os.path.getsize(output) / 1024 / 1024
    print(f"\nONNX saved: {output} ({size_mb:.1f} MB)")

    # Test inference voi onnxruntime
    print("\nTesting with onnxruntime CPU...")
    try:
        import onnxruntime as ort
        sess = ort.InferenceSession(output, providers=['CPUExecutionProvider'])
        x = np.random.rand(1, 3, 288, 288).astype(np.float32)
        y = sess.run(None, {sess.get_inputs()[0].name: x})[0]
        print(f"  Output: shape={y.shape}, min={y.min():.3f}, max={y.max():.3f}")
        print("  ONNX inference OK!")
    except Exception as e:
        print(f"  ONNX test failed: {e}")

    print("\n" + "=" * 50)
    print("XONG! Refresh trinh duyet tai http://localhost:8765 (hoac PORT ban da dat)")
    print("=" * 50)
