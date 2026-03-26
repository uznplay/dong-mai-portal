"""
Flask Web DocScanner - Chay local + ngrok
Cam on mobile: http://localhost:5000
"""

import os
import cv2
import numpy as np
import onnxruntime as ort
import torch
import torch.nn.functional as F
from flask import Flask, request, jsonify, send_file, render_template_string
from io import BytesIO
import base64
import uuid
import time

# ============ MODEL ============
MODEL_PATH = 'model_mobile/docscanner.onnx'
TEMP_DIR = 'web_temp'
os.makedirs(TEMP_DIR, exist_ok=True)


class DocScannerONNX:
    def __init__(self, model_path):
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self.session = ort.InferenceSession(model_path, sess_options=sess_options, providers=['CPUExecutionProvider'])
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        self.input_size = self.session.get_inputs()[0].shape[2]
        print(f"[DocScannerONNX] Model loaded: {self.input_size}x{self.input_size}")

    def scan(self, image_bgr):
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


# Load model
print("Loading model...")
scanner = DocScannerONNX(MODEL_PATH)
print("Ready!")

# ============ FLASK ============
app = Flask(__name__)


# ============ HTML ============
HTML = r"""
<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>DocScanner</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg: #0d0d0d;
    --surface: #1a1a1a;
    --surface2: #252525;
    --accent: #00d4ff;
    --accent2: #7c3aed;
    --text: #f0f0f0;
    --text2: #888;
    --green: #22c55e;
    --red: #ef4444;
  }

  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100dvh;
    display: flex;
    flex-direction: column;
  }

  header {
    padding: 16px 20px;
    display: flex;
    align-items: center;
    gap: 12px;
    border-bottom: 1px solid #2a2a2a;
    background: var(--surface);
  }

  .logo {
    width: 36px;
    height: 36px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    flex-shrink: 0;
  }

  header h1 {
    font-size: 18px;
    font-weight: 600;
    letter-spacing: -0.3px;
  }

  header span {
    font-size: 12px;
    color: var(--text2);
    background: var(--surface2);
    padding: 2px 8px;
    border-radius: 20px;
    margin-left: auto;
  }

  main {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 20px;
    gap: 16px;
    max-width: 480px;
    margin: 0 auto;
    width: 100%;
  }

  /* Upload zone */
  .upload-zone {
    border: 2px dashed #333;
    border-radius: 16px;
    padding: 32px 20px;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
    background: var(--surface);
    position: relative;
  }

  .upload-zone:hover, .upload-zone.dragover {
    border-color: var(--accent);
    background: #1a1f2e;
  }

  .upload-zone input[type="file"] {
    display: none;
  }

  .upload-icon {
    font-size: 48px;
    margin-bottom: 12px;
  }

  .upload-zone p {
    color: var(--text2);
    font-size: 14px;
  }

  .upload-zone .hint {
    font-size: 12px;
    color: #555;
    margin-top: 6px;
  }

  /* Preview */
  .preview-area {
    display: none;
    flex-direction: column;
    gap: 12px;
  }

  .preview-area.show { display: flex; }

  .preview-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }

  .preview-card {
    background: var(--surface);
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #2a2a2a;
  }

  .preview-card .label {
    font-size: 11px;
    color: var(--text2);
    padding: 6px 10px;
    background: var(--surface2);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .preview-card img {
    width: 100%;
    aspect-ratio: 3/4;
    object-fit: cover;
    display: block;
  }

  .preview-full {
    background: var(--surface);
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #2a2a2a;
  }

  .preview-full .label {
    font-size: 11px;
    color: var(--text2);
    padding: 6px 10px;
    background: var(--surface2);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .preview-full img {
    width: 100%;
    display: block;
    max-height: 500px;
    object-fit: contain;
  }

  /* Buttons */
  .btn-row {
    display: flex;
    gap: 10px;
  }

  .btn {
    flex: 1;
    padding: 14px;
    border: none;
    border-radius: 12px;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
  }

  .btn-primary {
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    color: #fff;
  }

  .btn-primary:hover { opacity: 0.9; }
  .btn-primary:active { transform: scale(0.98); }

  .btn-secondary {
    background: var(--surface2);
    color: var(--text);
    border: 1px solid #333;
  }

  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn .spinner {
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255,255,255,0.3);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  /* Status */
  .status-bar {
    background: var(--surface);
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 13px;
    display: flex;
    align-items: center;
    gap: 8px;
    border: 1px solid #2a2a2a;
  }

  .status-bar.ok { border-color: #22c55e33; }
  .status-bar.err { border-color: #ef444433; }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--text2);
    flex-shrink: 0;
  }

  .status-bar.ok .status-dot { background: var(--green); }
  .status-bar.err .status-dot { background: var(--red); }

  /* Info section */
  .info-section {
    background: var(--surface);
    border-radius: 12px;
    padding: 14px;
    border: 1px solid #2a2a2a;
  }

  .info-row {
    display: flex;
    justify-content: space-between;
    font-size: 13px;
    padding: 4px 0;
  }

  .info-row .key { color: var(--text2); }
  .info-row .val { color: var(--text); font-weight: 500; }
  .info-row .val.accent { color: var(--accent); }

  /* Download link */
  .download-link {
    display: none;
    text-align: center;
    padding: 14px;
    background: #22c55e15;
    border: 1px solid #22c55e33;
    border-radius: 12px;
    text-decoration: none;
    color: var(--green);
    font-weight: 600;
    font-size: 14px;
    transition: all 0.15s;
  }

  .download-link.show { display: block; }
  .download-link:hover { background: #22c55e25; }

  /* Image input button */
  .img-input-btn {
    background: var(--surface2);
    border: 1px solid #333;
    border-radius: 12px;
    padding: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    font-size: 15px;
    font-weight: 600;
    color: var(--text);
    cursor: pointer;
    transition: all 0.15s;
  }

  .img-input-btn:hover { background: #2a2a2a; }
  .img-input-btn:active { transform: scale(0.98); }
</style>
</head>
<body>

<header>
  <div class="logo">📄</div>
  <h1>DocScanner</h1>
  <span id="status-chip">Ready</span>
</header>

<main>

  <div id="upload-zone" class="upload-zone">
    <div class="upload-icon">📷</div>
    <p>Nhấn hoặc kéo thả ảnh vào đây</p>
    <p class="hint">JPG, PNG, WEBP • Tối đa 20MB</p>
    <input type="file" id="file-input" accept="image/*">
  </div>

  <div class="preview-area" id="preview-area">

    <div class="preview-full">
      <div class="label" id="result-label">Kết quả</div>
      <img id="result-img" src="" alt="Result">
    </div>

    <div class="preview-row">
      <div class="preview-card">
        <div class="label">Gốc</div>
        <img id="orig-img" src="" alt="Original">
      </div>
      <div class="preview-card">
        <div class="label">Đã scan</div>
        <img id="scan-img" src="" alt="Scanned">
      </div>
    </div>

    <div id="status-bar" class="status-bar">
      <div class="status-dot"></div>
      <span id="status-text">Đang xử lý...</span>
    </div>

    <div class="btn-row">
      <button class="btn btn-secondary" onclick="resetAll()">🗑️ Xoá</button>
      <button class="btn btn-primary" id="download-btn">
        ⬇️ Tải về
      </button>
    </div>

    <a id="dl-link" class="download-link" href="" download="scanned.png">
      ⬇️ Nhấn để tải ảnh đã scan
    </a>

  </div>

  <div class="info-section">
    <div class="info-row">
      <span class="key">Model</span>
      <span class="val accent">DocScanner ONNX</span>
    </div>
    <div class="info-row">
      <span class="key">Kích thước</span>
      <span class="val">32.4 MB</span>
    </div>
    <div class="info-row">
      <span class="key">Platform</span>
      <span class="val">CPU (onnxruntime)</span>
    </div>
    <div class="info-row">
      <span class="key">Input size</span>
      <span class="val">288×288</span>
    </div>
  </div>

</main>

<script>
const uploadZone = document.getElementById('upload-zone');
const fileInput = document.getElementById('file-input');
const previewArea = document.getElementById('preview-area');
const origImg = document.getElementById('orig-img');
const scanImg = document.getElementById('scan-img');
const resultImg = document.getElementById('result-img');
const resultLabel = document.getElementById('result-label');
const statusBar = document.getElementById('status-bar');
const statusText = document.getElementById('status-text');
const statusChip = document.getElementById('status-chip');
const dlLink = document.getElementById('dl-link');
const downloadBtn = document.getElementById('download-btn');
let currentResultData = null;

function setStatus(msg, type) {
  statusText.textContent = msg;
  statusBar.className = 'status-bar ' + type;
  statusChip.textContent = type === 'ok' ? 'Done' : type === 'err' ? 'Error' : 'Busy';
}

// Upload zone
uploadZone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', e => { if (e.target.files[0]) handleFile(e.target.files[0]); });

uploadZone.addEventListener('dragover', e => { e.preventDefault(); uploadZone.classList.add('dragover'); });
uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('dragover'));
uploadZone.addEventListener('drop', e => {
  e.preventDefault();
  uploadZone.classList.remove('dragover');
  if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
});

async function handleFile(file) {
  if (!file.type.startsWith('image/')) {
    setStatus('File khong hop le!', 'err');
    return;
  }

  // Show original
  const origData = await readFileAsDataURL(file);
  origImg.src = origData;
  scanImg.src = '';
  resultImg.src = '';
  dlLink.classList.remove('show');
  downloadBtn.disabled = true;
  previewArea.classList.add('show');
  setStatus('Đang upload & xử lý...', '');

  // Send to server
  const formData = new FormData();
  formData.append('image', file);

  const t0 = performance.now();

  try {
    const resp = await fetch('/scan', { method: 'POST', body: formData });
    const data = await resp.json();
    const elapsed = (performance.now() - t0).toFixed(0);

    if (data.error) {
      setStatus('Loi: ' + data.error, 'err');
      resultLabel.textContent = 'Lỗi!';
      return;
    }

    resultImg.src = data.image;
    scanImg.src = data.image;
    dlLink.href = data.image;
    dlLink.classList.add('show');
    downloadBtn.disabled = false;
    currentResultData = data.image;

    setStatus(`Xong trong ${elapsed}ms`, 'ok');
    resultLabel.textContent = 'Kết quả ✓';
  } catch (e) {
    setStatus('Loi ket noi: ' + e.message, 'err');
    resultLabel.textContent = 'Lỗi!';
  }
}

function readFileAsDataURL(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = e => resolve(e.target.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function resetAll() {
  previewArea.classList.remove('show');
  scanImg.src = '';
  resultImg.src = '';
  origImg.src = '';
  dlLink.classList.remove('show');
  downloadBtn.disabled = true;
  fileInput.value = '';
  currentResultData = null;
  setStatus('Ready', '');
  statusChip.textContent = 'Ready';
}

downloadBtn.addEventListener('click', () => {
  if (currentResultData) {
    dlLink.click();
  }
});
</script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML)


@app.route('/scan', methods=['POST'])
def scan_api():
    t0 = time.time()

    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    file = request.files['image']
    if not file.filename:
        return jsonify({'error': 'Empty file'}), 400

    # Read image
    raw = file.read()
    nparr = np.frombuffer(raw, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        return jsonify({'error': 'Cannot decode image'}), 400

    # Scan
    result = scanner.scan(image)
    elapsed = time.time() - t0
    print(f"[{elapsed*1000:.0f}ms] Scanned: {file.filename} {image.shape}")

    # Encode to base64
    _, buf = cv2.imencode('.png', result)
    b64 = base64.b64encode(buf).decode('utf-8')
    data_url = f'data:image/png;base64,{b64}'

    return jsonify({
        'image': data_url,
        'elapsed_ms': round(elapsed * 1000),
        'size': result.shape
    })


if __name__ == '__main__':
    print("=" * 50)
    print("DOCSCANNER WEB APP")
    print("=" * 50)
    print("Open: http://localhost:5000")
    print("Share via ngrok: ngrok http 5000")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=False)
