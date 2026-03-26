"""
Flask API Server - Chạy model trên server GPU, mobile chỉ gọi API
Cách này đơn giản nhất và đảm bảo chạy mượt trên mobile
"""

from flask import Flask, request, jsonify, send_file
import torch
import numpy as np
from PIL import Image
import cv2
import io
import base64
import os
import sys

# Add project path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from inference import Net, reload_seg_model, reload_rec_model

app = Flask(__name__)

# Global model
model = None


def load_model():
    """Load model khi server start"""
    global model
    print("Loading model...")
    model = Net()
    
    # Load pretrained weights
    seg_path = './model_pretrained/seg.pth'
    rec_path = './model_pretrained/DocScanner-L.pth'
    
    if os.path.exists(seg_path):
        model.msk = reload_seg_model(model.msk, seg_path)
    
    if os.path.exists(rec_path):
        model.bm = reload_rec_model(model.bm, rec_path)
    
    model.eval()
    print("Model loaded!")


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'model': 'loaded' if model else 'not_loaded'})


@app.route('/predict', methods=['POST'])
def predict():
    """
    API endpoint để scan document
    
    Request:
        - image: file ảnh (multipart/form-data)
        - Hoặc image_base64: ảnh dạng base64 (application/json)
    
    Response:
        - Trả về ảnh đã scan
    """
    global model
    
    try:
        # Đọc ảnh từ request
        if request.content_type and 'multipart/form-data' in request.content_type:
            if 'image' not in request.files:
                return jsonify({'error': 'No image provided'}), 400
            file = request.files['image']
            img_bytes = file.read()
        else:
            # JSON request với base64
            data = request.json
            if 'image_base64' not in data:
                return jsonify({'error': 'No image_base64 provided'}), 400
            
            img_bytes = base64.b64decode(data['image_base64'])
        
        # Decode ảnh
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return jsonify({'error': 'Invalid image'}), 400
        
        # Preprocess
        im_ori = img[:, :, :3].astype(np.float32) / 255.0
        h, w, _ = im_ori.shape
        im = cv2.resize(im_ori, (288, 288))
        im = im.transpose(2, 0, 1)
        im_tensor = torch.from_numpy(im).float().unsqueeze(0)
        
        # Inference
        if model is None:
            return jsonify({'error': 'Model not loaded'}), 500
        
        with torch.no_grad():
            bm = model(im_tensor)
            bm = bm.cpu()
            
            # Process output
            bm0 = cv2.resize(bm[0, 0].numpy(), (w, h))
            bm1 = cv2.resize(bm[0, 1].numpy(), (w, h))
            bm0 = cv2.blur(bm0, (3, 3))
            bm1 = cv2.blur(bm1, (3, 3))
            lbl = torch.from_numpy(np.stack([bm0, bm1], axis=2)).unsqueeze(0)
            
            import torch.nn.functional as F
            out = F.grid_sample(
                torch.from_numpy(im_ori).permute(2, 0, 1).unsqueeze(0).float(),
                lbl, align_corners=True
            )
            
            result = (((out[0] * 255).permute(1, 2, 0).numpy())[:, :, ::-1]).astype(np.uint8)
        
        # Encode kết quả
        _, buffer = cv2.imencode('.png', result)
        result_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            'success': True,
            'image': result_base64
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/predict_file', methods=['POST'])
def predict_file():
    """API trả về file ảnh trực tiếp"""
    global model
    
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        img_bytes = file.read()
        
        # Decode ảnh
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Preprocess
        im_ori = img[:, :, :3].astype(np.float32) / 255.0
        h, w, _ = im_ori.shape
        im = cv2.resize(im_ori, (288, 288))
        im = im.transpose(2, 0, 1)
        im_tensor = torch.from_numpy(im).float().unsqueeze(0)
        
        # Inference
        with torch.no_grad():
            bm = model(im_tensor)
            bm = bm.cpu()
            
            bm0 = cv2.resize(bm[0, 0].numpy(), (w, h))
            bm1 = cv2.resize(bm[0, 1].numpy(), (w, h))
            bm0 = cv2.blur(bm0, (3, 3))
            bm1 = cv2.blur(bm1, (3, 3))
            lbl = torch.from_numpy(np.stack([bm0, bm1], axis=2)).unsqueeze(0)
            
            import torch.nn.functional as F
            out = F.grid_sample(
                torch.from_numpy(im_ori).permute(2, 0, 1).unsqueeze(0).float(),
                lbl, align_corners=True
            )
            
            result = (((out[0] * 255).permute(1, 2, 0).numpy())[:, :, ::-1]).astype(np.uint8)
        
        # Trả về file
        _, buffer = cv2.imencode('.png', result)
        return send_file(
            io.BytesIO(buffer),
            mimetype='image/png',
            as_attachment=True,
            download_name='scanned.png'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Mobile client example (Flutter/Dart)
MOBILE_CLIENT_EXAMPLE = '''
// Flutter Client Example
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';

class DocumentScannerAPI {
  final String baseUrl;
  
  DocumentScannerAPI({required this.baseUrl});
  
  // Upload và nhận kết quả
  Future<File?> scanDocument(File imageFile) async {
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/predict_file'),
      );
      
      request.files.add(
        await http.MultipartFile.fromPath('image', imageFile.path),
      );
      
      var streamedResponse = await request.send();
      var response = await http.Response.fromStream(streamedResponse);
      
      if (response.statusCode == 200) {
        // Lưu ảnh kết quả
        final bytes = response.bodyBytes;
        final file = File('${imageFile.path}_scanned.png');
        await file.writeAsBytes(bytes);
        return file;
      }
      
      return null;
    } catch (e) {
      print('Error: $e');
      return null;
    }
  }
  
  // Upload base64 (cho web)
  Future<String?> scanDocumentBase64(String base64Image) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/predict'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'image_base64': base64Image}),
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data['image']; // Trả về base64 của ảnh kết quả
      }
      
      return null;
    } catch (e) {
      print('Error: $e');
      return null;
    }
  }
}

// Sử dụng:
/*
void main() async {
  final api = DocumentScannerAPI(baseUrl: 'https://your-server.com');
  final picker = ImagePicker();
  
  final image = await picker.pickImage(source: ImageSource.camera);
  if (image != null) {
    final result = await api.scanDocument(File(image.path));
    if (result != null) {
      print('Scanned: ${result.path}');
    }
  }
}
*/
'''


if __name__ == '__main__':
    # Load model khi start server
    load_model()
    
    # Chạy server
    # production: dùng gunicorn hoặc waitress
    # development: dùng Flask debug mode
    app.run(host='0.0.0.0', port=5000, debug=False)
    
    # Production command:
    # waitress-serve --host 0.0.0.0 --port 5000 app:app
