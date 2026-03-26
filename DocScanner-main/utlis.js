/**
 * utlis.js - OpenCV-style pre-processing for DocScanner (browser, no dependencies)
 *
 * Pipeline: Grayscale → Blur → Canny → Dilate/Erode → Contours
 *          → Biggest 4-pt contour → Perspective warp
 *
 * Usage: <script src="utlis.js"> in HTML, then window.utlis.*
 */

// ================================================================
//  Canvas helpers
// ================================================================
const utlis = {
  canvas(w, h) {
    const c = document.createElement('canvas');
    c.width = w; c.height = h;
    return { canvas: c, ctx: c.getContext('2d') };
  },

  /** Load image from dataUrl → { imgData, w, h } */
  async imageDataFromDataURL(dataUrl) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        const { canvas: c, ctx } = this.canvas(img.width, img.height);
        ctx.drawImage(img, 0, 0);
        resolve({ imgData: ctx.getImageData(0, 0, c.width, c.height), w: c.width, h: c.height });
      };
      img.onerror = reject;
      img.src = dataUrl;
    });
  },

  /** Load image from File → { imgData, w, h } */
  async imageDataFromFile(file) {
    const dataUrl = await new Promise((res, rej) => {
      const r = new FileReader();
      r.onload = e => res(e.target.result);
      r.onerror = rej;
      r.readAsDataURL(file);
    });
    return this.imageDataFromDataURL(dataUrl);
  },

  // ================================================================
  //  Image processing
  // ================================================================

  /** Convert ImageData (RGBA) → grayscale Uint8 (0-255) */
  toGrayscale(imgData) {
    const { data, width: w, height: h } = imgData;
    const gray = new Uint8Array(w * h);
    for (let i = 0; i < w * h; i++) {
      gray[i] = Math.round(0.299 * data[i*4] + 0.587 * data[i*4+1] + 0.114 * data[i*4+2]);
    }
    return { gray, w, h };
  },

  /**
   * 2D convolution → Uint8 [0,255] (chỉ dùng cho kernel không âm, ví dụ box blur đơn giản)
   */
  _convolve2D(gray, w, h, kernel, kSize, normalize) {
    const out = new Uint8Array(w * h);
    const half = Math.floor(kSize / 2);
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        let sum = 0;
        for (let ky = -half; ky <= half; ky++) {
          for (let kx = -half; kx <= half; kx++) {
            const nx = Math.min(Math.max(x+kx, 0), w-1);
            const ny = Math.min(Math.max(y+ky, 0), h-1);
            sum += gray[ny*w+nx] * kernel[(ky+half)*kSize+(kx+half)];
          }
        }
        const v = normalize ? sum / (kSize * kSize) : sum;
        out[y*w+x] = Math.max(0, Math.min(255, Math.round(v)));
      }
    }
    return out;
  },

  /** Gaussian 5x5 — chia 273 rồi clamp (KHÔNG clamp sum trước khi chia) */
  gaussianBlur(gray, w, h) {
    const k = [1,4,7,4,1, 4,16,26,16,4, 7,26,41,26,7, 4,16,26,16,4, 1,4,7,4,1];
    const div = 273;
    const out = new Uint8Array(w * h);
    const half = 2;
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        let sum = 0;
        for (let ky = -half; ky <= half; ky++) {
          for (let kx = -half; kx <= half; kx++) {
            const nx = Math.min(Math.max(x+kx, 0), w-1);
            const ny = Math.min(Math.max(y+ky, 0), h-1);
            sum += gray[ny*w+nx] * k[(ky+half)*5+(kx+half)];
          }
        }
        out[y*w+x] = Math.max(0, Math.min(255, Math.round(sum / div)));
      }
    }
    return out;
  },

  /** Sobel / kernel có dấu — trả về Float32 (giữ giá trị âm) */
  _convolve2DFloat(gray, w, h, kernel, kSize) {
    const out = new Float32Array(w * h);
    const half = Math.floor(kSize / 2);
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        let sum = 0;
        for (let ky = -half; ky <= half; ky++) {
          for (let kx = -half; kx <= half; kx++) {
            const nx = Math.min(Math.max(x+kx, 0), w-1);
            const ny = Math.min(Math.max(y+ky, 0), h-1);
            sum += gray[ny*w+nx] * kernel[(ky+half)*kSize+(kx+half)];
          }
        }
        out[y*w+x] = sum;
      }
    }
    return out;
  },

  /** Median blur 3x3 */
  medianBlur(gray, w, h) {
    const out = new Uint8Array(w*h);
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const vals = [];
        for (let dy = -1; dy <= 1; dy++) {
          for (let dx = -1; dx <= 1; dx++) {
            vals.push(gray[Math.min(Math.max(y+dy,0),h-1)*w+Math.min(Math.max(x+dx,0),w-1)]);
          }
        }
        vals.sort((a,b)=>a-b);
        out[y*w+x] = vals[4];
      }
    }
    return out;
  },

  /**
   * Canny edge detection → { edges, w, h }
   * @param {boolean} alreadyBlurred - true nếu gray đã là Gaussian blur (tránh blur 2 lần)
   */
  cannyEdges(gray, w, h, t1, t2, alreadyBlurred = false) {
    if (t2 < t1) { const s = t1; t1 = t2; t2 = s; }
    const gxK = [-1,0,1,-2,0,2,-1,0,1];
    const gyK = [-1,-2,-1,0,0,0,1,2,1];
    const blur = alreadyBlurred ? gray : this.gaussianBlur(gray, w, h);
    const gx = this._convolve2DFloat(blur, w, h, gxK, 3);
    const gy = this._convolve2DFloat(blur, w, h, gyK, 3);
    const mag = new Float32Array(w*h), dir = new Float32Array(w*h);
    for (let i = 0; i < w*h; i++) {
      mag[i] = Math.sqrt(gx[i]*gx[i]+gy[i]*gy[i]);
      const d = Math.atan2(gy[i], gx[i])*180/Math.PI;
      if      (d>=-22.5&&d<22.5) dir[i]=0;
      else if (d>=22.5&&d<67.5) dir[i]=1;
      else if (d>=67.5&&d<112.5) dir[i]=2;
      else if (d>=-67.5&&d<-22.5) dir[i]=3;
      else if (d>=112.5||d<-112.5) dir[i]=0;
      else dir[i]=3;
    }
    // NMS + hai ngưỡng: 0 = không cạnh, 1 = yếu, 2 = mạnh (Canny đúng chuẩn cần nối yếu→mạnh)
    const label = new Uint8Array(w * h);
    for (let y = 1; y < h - 1; y++) {
      for (let x = 1; x < w - 1; x++) {
        const i = y * w + x;
        if (mag[i] < t1) continue;
        let m1 = 0, m2 = 0;
        if (dir[i] === 0) { m1 = mag[i - 1]; m2 = mag[i + 1]; }
        else if (dir[i] === 1) { m1 = mag[i - w + 1]; m2 = mag[i + w - 1]; }
        else if (dir[i] === 2) { m1 = mag[i - w]; m2 = mag[i + w]; }
        else { m1 = mag[i - w - 1]; m2 = mag[i + w + 1]; }
        if (!(mag[i] >= m1 && mag[i] >= m2)) continue;
        label[i] = mag[i] >= t2 ? 2 : 1;
      }
    }
    const out = new Uint8Array(w * h);
    const q = [];
    let hadStrong = false;
    for (let i = 0; i < w * h; i++) {
      if (label[i] === 2) {
        hadStrong = true;
        out[i] = 255;
        q.push(i);
      }
    }
    // Không có cạnh “mạnh” (≥ t2): hysteresis không có hạt giống — dùng một ngưỡng (mọi điểm qua NMS và ≥ t1)
    if (!hadStrong) {
      for (let i = 0; i < w * h; i++) {
        if (label[i] === 1) out[i] = 255;
      }
      return { edges: out, w, h };
    }
    const pushWeak = (j) => {
      if (j < 0 || j >= w * h || label[j] !== 1 || out[j]) return;
      out[j] = 255;
      label[j] = 2;
      q.push(j);
    };
    while (q.length) {
      const i = q.pop();
      const x = i % w, y = (i / w) | 0;
      for (let dy = -1; dy <= 1; dy++) {
        for (let dx = -1; dx <= 1; dx++) {
          if (dx === 0 && dy === 0) continue;
          const nx = x + dx, ny = y + dy;
          if (nx < 0 || nx >= w || ny < 0 || ny >= h) continue;
          pushWeak(ny * w + nx);
        }
      }
    }
    return { edges: out, w, h };
  },

  /** Dilate */
  dilate(edges, w, h, kSize=5, iterations=2) {
    return this._morph(edges, w, h, kSize, iterations, 'dilate');
  },

  /** Erode */
  erode(edges, w, h, kSize=5, iterations=1) {
    return this._morph(edges, w, h, kSize, iterations, 'erode');
  },

  _morph(src, w, h, kSize, iterations, op) {
    let data = src.slice();
    const half = Math.floor(kSize/2);
    for (let iter=0; iter<iterations; iter++) {
      const out = new Uint8Array(w*h);
      for (let y=0; y<h; y++) {
        for (let x=0; x<w; x++) {
          const vals=[];
          for (let ky=-half; ky<=half; ky++) {
            for (let kx=-half; kx<=half; kx++) {
              vals.push(data[Math.min(Math.max(y+ky,0),h-1)*w+Math.min(Math.max(x+kx,0),w-1)]);
            }
          }
          vals.sort((a,b)=>a-b);
          out[y*w+x]=(op==='dilate')?vals[vals.length-1]:vals[0];
        }
      }
      data=out;
    }
    return data;
  },

  /** Adaptive threshold → { bin, w, h } */
  adaptiveThreshold(gray, w, h, C=2, blockSize=7) {
    const out = new Uint8Array(w*h);
    const half = Math.floor(blockSize/2);
    for (let y=0; y<h; y++) {
      for (let x=0; x<w; x++) {
        let sum=0,cnt=0;
        for (let ky=-half; ky<=half; ky++) {
          for (let kx=-half; kx<=half; kx++) {
            sum+=gray[Math.min(Math.max(y+ky,0),h-1)*w+Math.min(Math.max(x+kx,0),w-1)];
            cnt++;
          }
        }
        out[y*w+x]=(gray[y*w+x] > Math.round(sum/cnt)-C)?255:0;
      }
    }
    return { bin: out, w, h };
  },

  invert(bin) { return bin.map(v=>255-v); },

  // ================================================================
  //  Contour detection
  // ================================================================

  /** Find all contours (8-connectivity, RETR_EXTERNAL equivalent) */
  findContours(edges, w, h) {
    const visited = new Uint8Array(w*h);
    const contours = [];
    const N8 = [[-1,0],[-1,1],[0,1],[1,1],[1,0],[1,-1],[0,-1],[-1,-1]];
    function dfs(x, y, contour) {
      const stack = [[x,y]];
      while (stack.length) {
        const [cx,cy] = stack.pop();
        if (cx<0||cx>=w||cy<0||cy>=h) continue;
        const idx=cy*w+cx;
        if (visited[idx]||edges[idx]===0) continue;
        visited[idx]=1;
        contour.push([cx,cy]);
        for (const [dx,dy] of N8) stack.push([cx+dx,cy+dy]);
      }
    }
    for (let y=0; y<h; y++) {
      for (let x=0; x<w; x++) {
        if (edges[y*w+x]>0&&!visited[y*w+x]) {
          const c=[];
          dfs(x,y,c);
          if (c.length>=5) contours.push(c);
        }
      }
    }
    return contours;
  },

  /** Douglas-Peucker simplification */
  _simplify(pts, eps) {
    if (pts.length<3) return pts;
    const first=pts[0], last=pts[pts.length-1];
    let maxD=0, maxI=0;
    for (let i=1;i<pts.length-1;i++) {
      const d=this._perpDist(pts[i],first,last);
      if (d>maxD){maxD=d;maxI=i;}
    }
    if (maxD>eps) {
      const left=this._simplify(pts.slice(0,maxI+1),eps);
      const right=this._simplify(pts.slice(maxI),eps);
      return [...left.slice(0,-1),...right];
    }
    return [first,last];
  },

  _perpDist(p,a,b) {
    const dx=b[0]-a[0], dy=b[1]-a[1];
    const len=Math.sqrt(dx*dx+dy*dy);
    if (len===0) return Math.sqrt((p[0]-a[0])**2+(p[1]-a[1])**2);
    return Math.abs((b[1]-a[1])*p[0]-(b[0]-a[0])*p[1]+b[0]*a[1]-b[1]*a[0])/len;
  },

  _contourArea(pts) {
    let a=0;
    for (let i=0;i<pts.length;i++) {
      const j=(i+1)%pts.length;
      a+=pts[i][0]*pts[j][1]-pts[j][0]*pts[i][1];
    }
    return Math.abs(a/2);
  },

  _contourPerimeter(pts) {
    let p=0;
    for (let i=0;i<pts.length;i++) {
      const j=(i+1)%pts.length;
      p+=Math.sqrt((pts[j][0]-pts[i][0])**2+(pts[j][1]-pts[i][1])**2);
    }
    return p;
  },

  /** Convex hull (monotone chain), CCW */
  convexHull(points) {
    const seen = new Set();
    const uniq = [];
    for (const p of points) {
      const k = `${p[0]},${p[1]}`;
      if (seen.has(k)) continue;
      seen.add(k);
      uniq.push([p[0], p[1]]);
    }
    if (uniq.length < 3) return uniq.slice();
    uniq.sort((a, b) => (a[0] === b[0] ? a[1] - b[1] : a[0] - b[0]));
    const cross = (o, a, b) =>
      (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
    const lower = [];
    for (const p of uniq) {
      while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], p) <= 0) lower.pop();
      lower.push(p);
    }
    const upper = [];
    for (let i = uniq.length - 1; i >= 0; i--) {
      const p = uniq[i];
      while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], p) <= 0) upper.pop();
      upper.push(p);
    }
    upper.pop();
    lower.pop();
    return lower.concat(upper);
  },

  /** Tương tự cv2.minAreaRect + boxPoints: 4 góc bao nhỏ nhất quanh convex hull */
  minAreaRectQuad(hull) {
    const n = hull.length;
    if (n < 3) return null;
    let minArea = Infinity;
    let best = null;
    for (let i = 0; i < n; i++) {
      const p0 = hull[i], p1 = hull[(i + 1) % n];
      const ux = p1[0] - p0[0], uy = p1[1] - p0[1];
      const len = Math.hypot(ux, uy);
      if (len < 1e-10) continue;
      const ex = ux / len, ey = uy / len;
      const nx = -ey, ny = ex;
      let minP = Infinity, maxP = -Infinity, minS = Infinity, maxS = -Infinity;
      for (const p of hull) {
        const vx = p[0] - p0[0], vy = p[1] - p0[1];
        const proj = vx * ex + vy * ey;
        const s = vx * nx + vy * ny;
        minP = Math.min(minP, proj);
        maxP = Math.max(maxP, proj);
        minS = Math.min(minS, s);
        maxS = Math.max(maxS, s);
      }
      const area = (maxP - minP) * (maxS - minS);
      if (area < minArea && area > 1e-6) {
        minArea = area;
        best = [
          [p0[0] + minP * ex + minS * nx, p0[1] + minP * ey + minS * ny],
          [p0[0] + maxP * ex + minS * nx, p0[1] + maxP * ey + minS * ny],
          [p0[0] + maxP * ex + maxS * nx, p0[1] + maxP * ey + maxS * ny],
          [p0[0] + minP * ex + maxS * nx, p0[1] + minP * ey + maxS * ny],
        ];
      }
    }
    return best;
  },

  _quadArea(quad) {
    if (!quad || quad.length !== 4) return 0;
    let a = 0;
    for (let i = 0; i < 4; i++) {
      const j = (i + 1) % 4;
      a += quad[i][0] * quad[j][1] - quad[j][0] * quad[i][1];
    }
    return Math.abs(a / 2);
  },

  /**
   * Contour từ DFS không thứ tự như OpenCV — không dùng được shoelace + approxPolyDP.
   * Lấy convex hull → minAreaRect (4 góc), chọn contour có diện tích HCN nhỏ nhất lớn nhất (tài liệu lớn nhất).
   */
  biggestContour(contours, minArea = 3000) {
    let best = null, bestA = 0;
    for (const raw of contours) {
      if (raw.length < 30) continue;
      const hull = this.convexHull(raw);
      if (hull.length < 3) continue;
      const quad = this.minAreaRectQuad(hull);
      if (!quad) continue;
      const area = this._quadArea(quad);
      if (area < minArea) continue;
      if (area > bestA) {
        best = quad;
        bestA = area;
      }
    }
    return best;
  },

  /** Reorder 4 points → TL, TR, BR, BL */
  reorder4(pts) {
    const s = pts.slice().sort((a,b)=>(a[0]+a[1])-(b[0]+b[1]));
    const tl=s[0], br=s[3];
    const mid=[s[1],s[2]].sort((a,b)=>(a[0]-a[1])-(b[0]-b[1]));
    return [tl, mid[0], br, mid[1]];
  },

  // ================================================================
  //  Perspective warp
  // ================================================================

  /**
   * Perspective warp: 4 góc nguồn → HCN đích (TL,TR,BR,BL).
   * Trước đây sai cặp điểm (src thô vs dst đã reorder) + sai cách áp H → ảnh đen.
   */
  perspectiveWarp(srcData, srcW, srcH, srcPts4) {
    const src = this.reorder4(srcPts4);
    const [tl, tr, br, bl] = src;
    const wTop = Math.hypot(tr[0] - tl[0], tr[1] - tl[1]);
    const wBot = Math.hypot(br[0] - bl[0], br[1] - bl[1]);
    const hL = Math.hypot(bl[0] - tl[0], bl[1] - tl[1]);
    const hR = Math.hypot(br[0] - tr[0], br[1] - tr[1]);
    const dstW = Math.round(Math.max(wTop, wBot));
    const dstH = Math.round(Math.max(hL, hR));
    if (dstW < 10 || dstH < 10) return null;

    const wm = Math.max(dstW - 1, 1);
    const hm = Math.max(dstH - 1, 1);
    const dst = [
      [0, 0],
      [wm, 0],
      [wm, hm],
      [0, hm],
    ];

    const H = this._homographyFrom4Pairs(src, dst);
    if (!H) return null;
    const inv = this._invert3x3(H);
    if (!inv) return null;

    const out = new Uint8ClampedArray(dstW * dstH * 4);
    for (let dy = 0; dy < dstH; dy++) {
      for (let dx = 0; dx < dstW; dx++) {
        const p = this._applyHomography(inv, dx, dy);
        const o = (dy * dstW + dx) * 4;
        if (p) {
          const s = this._sampleBilinearRGBA(srcData, srcW, srcH, p[0], p[1]);
          out[o] = s[0];
          out[o + 1] = s[1];
          out[o + 2] = s[2];
          out[o + 3] = s[3];
        }
      }
    }
    return { data: out, w: dstW, h: dstH };
  },

  /** H (3x3, h22=1) sao cho H*[sx,sy,1] ~ k*[dx,dy,1] — 4 cặp cùng thứ tự TL,TR,BR,BL */
  _homographyFrom4Pairs(src4, dst4) {
    const n = 8;
    const A = [];
    const b = new Array(n);
    for (let i = 0; i < 4; i++) {
      const [x, y] = src4[i];
      const [u, v] = dst4[i];
      const r0 = i * 2;
      A[r0] = [x, y, 1, 0, 0, 0, -u * x, -u * y];
      b[r0] = u;
      A[r0 + 1] = [0, 0, 0, x, y, 1, -v * x, -v * y];
      b[r0 + 1] = v;
    }
    const h8 = this._solve8(A, b);
    if (!h8) return null;
    return [h8[0], h8[1], h8[2], h8[3], h8[4], h8[5], h8[6], h8[7], 1];
  },

  _solve8(A, b) {
    const M = A.map((row, i) => [...row, b[i]]);
    const n = 8;
    for (let col = 0; col < n; col++) {
      let piv = col;
      for (let r = col + 1; r < n; r++) {
        if (Math.abs(M[r][col]) > Math.abs(M[piv][col])) piv = r;
      }
      if (Math.abs(M[piv][col]) < 1e-12) return null;
      [M[col], M[piv]] = [M[piv], M[col]];
      const div = M[col][col];
      for (let k = col; k <= n; k++) M[col][k] /= div;
      for (let r = 0; r < n; r++) {
        if (r === col) continue;
        const f = M[r][col];
        for (let k = col; k <= n; k++) M[r][k] -= f * M[col][k];
      }
    }
    return M.map((row) => row[n]);
  },

  _invert3x3(m) {
    const a = m[0], b = m[1], c = m[2];
    const d = m[3], e = m[4], f = m[5];
    const g = m[6], h = m[7], i = m[8];
    const A = e * i - f * h;
    const B = -(d * i - f * g);
    const C = d * h - e * g;
    const D = -(b * i - c * h);
    const E = a * i - c * g;
    const F = -(a * h - b * g);
    const G = b * f - c * e;
    const H = -(a * f - c * d);
    const I = a * e - b * d;
    const det = a * A + b * B + c * C;
    if (Math.abs(det) < 1e-12) return null;
    const s = 1 / det;
    return [A * s, D * s, G * s, B * s, E * s, H * s, C * s, F * s, I * s];
  },

  _applyHomography(H9, x, y) {
    const X = H9[0] * x + H9[1] * y + H9[2];
    const Y = H9[3] * x + H9[4] * y + H9[5];
    const W = H9[6] * x + H9[7] * y + H9[8];
    if (Math.abs(W) < 1e-12) return null;
    return [X / W, Y / W];
  },

  _sampleBilinearRGBA(srcData, srcW, srcH, x, y) {
    if (!Number.isFinite(x) || !Number.isFinite(y)) return [0, 0, 0, 255];
    const cx = Math.max(0, Math.min(x, srcW - 1));
    const cy = Math.max(0, Math.min(y, srcH - 1));
    const x0 = Math.floor(cx);
    const y0 = Math.floor(cy);
    const x1 = Math.min(x0 + 1, srcW - 1);
    const y1 = Math.min(y0 + 1, srcH - 1);
    const wx = cx - x0;
    const wy = cy - y0;
    const w00 = (1 - wx) * (1 - wy);
    const w10 = wx * (1 - wy);
    const w01 = (1 - wx) * wy;
    const w11 = wx * wy;
    const o = (y0, x0) => (y0 * srcW + x0) * 4;
    const i00 = o(y0, x0);
    const i10 = o(y0, x1);
    const i01 = o(y1, x0);
    const i11 = o(y1, x1);
    const r =
      srcData[i00] * w00 + srcData[i10] * w10 + srcData[i01] * w01 + srcData[i11] * w11;
    const g =
      srcData[i00 + 1] * w00 + srcData[i10 + 1] * w10 + srcData[i01 + 1] * w01 + srcData[i11 + 1] * w11;
    const b =
      srcData[i00 + 2] * w00 + srcData[i10 + 2] * w10 + srcData[i01 + 2] * w01 + srcData[i11 + 2] * w11;
    const a =
      srcData[i00 + 3] * w00 + srcData[i10 + 3] * w10 + srcData[i01 + 3] * w01 + srcData[i11 + 3] * w11;
    return [Math.round(r), Math.round(g), Math.round(b), Math.round(a)];
  },

  // ================================================================
  //  Drawing helpers
  // ================================================================

  /** Draw grayscale → canvas */
  drawGrayscale(gray, w, h) {
    const { canvas, ctx } = this.canvas(w, h);
    const imgData = ctx.createImageData(w, h);
    for (let i=0;i<w*h;i++) {
      const g=gray[i];
      imgData.data[i*4]=g; imgData.data[i*4+1]=g; imgData.data[i*4+2]=g; imgData.data[i*4+3]=255;
    }
    ctx.putImageData(imgData, 0, 0);
    return canvas;
  },

  /** Draw binary edges → canvas */
  drawEdges(edges, w, h) { return this.drawGrayscale(edges, w, h); },

  /** Draw contours (green) on an offscreen canvas */
  drawContoursOnCanvas(imgData, w, h, contours, thickness=3) {
    const { canvas, ctx } = this.canvas(w, h);
    // First draw the image
    ctx.putImageData(imgData, 0, 0);
    ctx.strokeStyle='#00ff00'; ctx.lineWidth=thickness; ctx.lineJoin='round';
    for (const contour of contours) {
      if (contour.length<2) continue;
      ctx.beginPath();
      ctx.moveTo(contour[0][0], contour[0][1]);
      for (let i=1;i<contour.length;i++) ctx.lineTo(contour[i][0], contour[i][1]);
      ctx.stroke();
    }
    return canvas;
  },

  /** Draw 4 corner points + lines on canvas */
  draw4CornersOnCanvas(imgData, w, h, pts4, r=8) {
    const { canvas, ctx } = this.canvas(w, h);
    ctx.putImageData(imgData, 0, 0);
    const pts = this.reorder4(pts4);
    // Lines
    ctx.strokeStyle='#ff6600'; ctx.lineWidth=3;
    ctx.beginPath();
    for (let i=0;i<4;i++) {
      const [x1,y1]=pts[i],[x2,y2]=pts[(i+1)%4];
      i===0 ? ctx.moveTo(x1,y1) : ctx.lineTo(x1,y1);
    }
    ctx.closePath(); ctx.stroke();
    // Dots
    ctx.fillStyle='#ff0000';
    for (const [x,y] of pts) {
      ctx.beginPath(); ctx.arc(x,y,r,0,Math.PI*2); ctx.fill();
    }
    return canvas;
  },

  // ================================================================
  //  Canvas / Image conversion
  // ================================================================

  /** RGBA Uint8ClampedArray → canvas */
  rgbaToCanvas(data, w, h) {
    const { canvas, ctx } = this.canvas(w, h);
    const imgData = ctx.createImageData(w, h);
    imgData.data.set(data);
    ctx.putImageData(imgData, 0, 0);
    return canvas;
  },

  /** Canvas resize (bilinear) */
  resizeCanvas(sourceCanvas, dstW, dstH) {
    const { canvas, ctx } = this.canvas(dstW, dstH);
    ctx.drawImage(sourceCanvas, 0, 0, dstW, dstH);
    return canvas;
  },

  /** Canvas → Float32Array RGB [0,1] */
  canvasToRgbF32(canvasEl) {
    const w=canvasEl.width, h=canvasEl.height;
    const ctx=canvasEl.getContext('2d');
    const imgData=ctx.getImageData(0,0,w,h);
    const rgb=new Float32Array(w*h*3);
    for(let i=0;i<w*h;i++){
      rgb[i*3+0]=imgData.data[i*4+0]/255;
      rgb[i*3+1]=imgData.data[i*4+1]/255;
      rgb[i*3+2]=imgData.data[i*4+2]/255;
    }
    return { rgb, w, h };
  },

  /** Stack 2x2 canvases for preview */
  stack2x2(c11,c12,c21,c22,scale=0.4) {
    const cells=[[c11,c12],[c21,c22]];
    const sc=cells.map(row=>row.map(c=>this.resizeCanvas(c,Math.round(c.width*scale),Math.round(c.height*scale))));
    const sw=sc[0][0].width, sh=sc[0][0].height;
    const { canvas, ctx }=this.canvas(sw*2, sh*2);
    for(let r=0;r<2;r++) for(let c=0;c<2;c++) ctx.drawImage(sc[r][c],c*sw,r*sh);
    return canvas;
  },

  /** Stack canvases in a row */
  stackH(canvases, scale=0.4) {
    const sc=canvases.map(c=>this.resizeCanvas(c,Math.round(c.width*scale),Math.round(c.height*scale)));
    const sw=sc[0].width, sh=sc[0].height;
    const { canvas, ctx }=this.canvas(sw*sc.length, sh);
    sc.forEach((c,i)=>ctx.drawImage(c,i*sw,0));
    return canvas;
  },
};

window.utlis = utlis;
