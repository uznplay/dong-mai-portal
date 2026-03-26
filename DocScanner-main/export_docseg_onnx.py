"""
Export U2NETP (seg.pth) -> docseg.onnx cho ONNX Runtime Web (WASM).
Output: mask [B,1,H,W] sigmoid, không threshold (JS dùng > 0.5).
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import torch
import torch.nn as nn

from seg import U2NETP


def load_seg_weights(msk: nn.Module, seg_path: str) -> None:
    if not seg_path or not os.path.exists(seg_path):
        raise FileNotFoundError(f"Khong tim thay seg: {seg_path}")
    seg_dict = msk.state_dict()
    pretrained = torch.load(seg_path, map_location="cpu", weights_only=False)
    stripped = {k[6:]: v for k, v in pretrained.items() if k[6:] in seg_dict}
    if len(stripped) >= max(8, len(seg_dict) // 4):
        seg_dict.update(stripped)
    else:
        direct = {k: v for k, v in pretrained.items() if k in seg_dict}
        seg_dict.update(direct)
    msk.load_state_dict(seg_dict)


class U2NETPOut(nn.Module):
    def __init__(self, seg_path: str):
        super().__init__()
        self.msk = U2NETP(3, 1)
        load_seg_weights(self.msk, seg_path)

    def forward(self, x):
        m0, _, _, _, _, _, _ = self.msk(x)
        return m0


if __name__ == "__main__":
    seg_path = os.path.join("model_pretrained", "seg.pth")
    out_dir = "model_mobile"
    os.makedirs(out_dir, exist_ok=True)
    output = os.path.join(out_dir, "docseg.onnx")

    print("Export U2NETP ->", output)
    net = U2NETPOut(seg_path)
    net.eval()

    dummy = torch.randn(1, 3, 288, 288)
    torch.onnx.export(
        net,
        dummy,
        output,
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
    mb = os.path.getsize(output) / 1024 / 1024
    print(f"OK: {output} ({mb:.2f} MB)")

    try:
        import onnxruntime as ort

        sess = ort.InferenceSession(output, providers=["CPUExecutionProvider"])
        x = __import__("numpy").random.rand(1, 3, 288, 288).astype("float32")
        y = sess.run(None, {sess.get_inputs()[0].name: x})[0]
        print("Test ORT:", y.shape, y.min(), y.max())
    except Exception as e:
        print("ORT test skip:", e)
