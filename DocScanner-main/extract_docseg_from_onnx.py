"""
Extract msk (U2NETP) weights from docscanner.onnx and export as docseg.onnx.
Because seg.pth is corrupted (downloaded as PDF), we use the already-exported
docscanner.onnx which contains all mask weights.
"""
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import torch
import torch.nn as nn
import numpy as np
import onnx
from onnx import numpy_helper

from seg import U2NETP


def extract_msk_weights_from_onnx(onnx_path):
    """Load mask weights from docscanner.onnx."""
    model = onnx.load(onnx_path)
    weights = {}
    for init in model.graph.initializer:
        name = init.name
        if name.startswith("msk."):
            tensor = numpy_helper.to_array(init)
            weights[name[4:]] = tensor  # strip "msk." prefix
    return weights


class U2NETPOut(nn.Module):
    """U2NETP wrapper that returns only the main mask output (d0)."""
    def __init__(self, weights):
        super().__init__()
        self.msk = U2NETP(3, 1)
        torch_weights = {k: torch.from_numpy(v) for k, v in weights.items()}
        self.msk.load_state_dict(torch_weights, strict=False)
        self.msk.eval()

    def forward(self, x):
        d0, *_ = self.msk(x)
        return d0


if __name__ == "__main__":
    src_onnx = "model_mobile/docscanner.onnx"
    out_onnx = "model_mobile/docseg.onnx"

    print("Extracting msk weights from:", src_onnx)
    weights = extract_msk_weights_from_onnx(src_onnx)
    print(f"  Found {len(weights)} msk weights: {list(weights.keys())[:5]}...")

    # Check key weights exist
    needed = ['stage1.rebnconvin.conv_s1.weight', 'side1.weight', 'outconv.weight']
    for n in needed:
        if n not in weights:
            print(f"  [WARN] Missing: {n}")
        else:
            print(f"  [OK] {n}: {weights[n].shape}")

    print("\nBuilding U2NETPOut model...")
    model = U2NETPOut(weights)
    model.eval()

    # Test forward pass
    dummy = torch.randn(1, 3, 288, 288)
    with torch.no_grad():
        out = model(dummy)
    print(f"  Forward pass OK: output shape = {out.shape}")

    # Export
    print(f"\nExporting to {out_onnx}...")
    torch.onnx.export(
        model,
        dummy,
        out_onnx,
        export_params=True,
        opset_version=16,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["mask"],
        dynamic_axes={
            "input": {0: "batch", 2: "height", 3: "width"},
            "mask": {0: "batch", 2: "height", 3: "width"},
        },
    )
    mb = os.path.getsize(out_onnx) / 1024 / 1024
    print(f"  Saved: {out_onnx} ({mb:.2f} MB)")

    # Verify
    print("\nVerifying with onnxruntime...")
    try:
        import onnxruntime as ort
        sess = ort.InferenceSession(out_onnx, providers=["CPUExecutionProvider"])
        x = np.random.rand(1, 3, 288, 288).astype("float32")
        y = sess.run(None, {sess.get_inputs()[0].name: x})[0]
        print(f"  Output: shape={y.shape}, min={y.min():.4f}, max={y.max():.4f}")
        print("  ONNX inference OK!")
    except Exception as e:
        print(f"  ONNX test failed: {e}")

    print("\nDone!")
