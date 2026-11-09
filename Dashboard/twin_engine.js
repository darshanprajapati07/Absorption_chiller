/* In-browser forward pass of the trained LSTM ensemble (PyTorch gate order i, f, g, o).
   Same maths as ml/models.py: 2-layer LSTM -> Linear-tanh-Linear, run step by step. */
var TwinEngine = (function () {
  function decode(b64) {
    var bytes;
    if (typeof atob === 'function') {
      var s = atob(b64); bytes = new Uint8Array(s.length);
      for (var i = 0; i < s.length; i++) bytes[i] = s.charCodeAt(i);
    } else { bytes = new Uint8Array(Buffer.from(b64, 'base64')); }
    return new Float32Array(bytes.buffer, bytes.byteOffset, bytes.byteLength / 4);
  }

  function Member(buf, nIn, H, L, nOut) {
    var o = 0, take = function (n) { var a = buf.subarray(o, o + n); o += n; return a; };
    this.layers = [];
    for (var l = 0; l < L; l++) {
      var ni = l === 0 ? nIn : H;
      this.layers.push({ ni: ni, Wih: take(4 * H * ni), Whh: take(4 * H * H), b: take(4 * H) });
    }
    this.W1 = take(H * H); this.b1 = take(H); this.W2 = take(nOut * H); this.b2 = take(nOut);
    if (o !== buf.length) throw new Error('weight size mismatch ' + o + ' vs ' + buf.length);
    this.H = H; this.nOut = nOut; this.g = new Float64Array(4 * H); this.z = new Float64Array(H);
    this.reset();
  }
  Member.prototype.reset = function () {
    this.h = this.layers.map(function () { return new Float64Array(this.H); }, this);
    this.c = this.layers.map(function () { return new Float64Array(this.H); }, this);
  };
  function sig(v) { return 1 / (1 + Math.exp(-v)); }
  Member.prototype.step = function (x, out) {
    var H = this.H, g = this.g, inp = x;
    for (var l = 0; l < this.layers.length; l++) {
      var Ly = this.layers[l], ni = Ly.ni, h = this.h[l], c = this.c[l];
      for (var r = 0; r < 4 * H; r++) {
        var s = Ly.b[r], wi = r * ni, wh = r * H;
        for (var k = 0; k < ni; k++) s += Ly.Wih[wi + k] * inp[k];
        for (k = 0; k < H; k++) s += Ly.Whh[wh + k] * h[k];
        g[r] = s;
      }
      for (var j = 0; j < H; j++) {
        var ig = sig(g[j]), fg = sig(g[H + j]), gg = Math.tanh(g[2 * H + j]), og = sig(g[3 * H + j]);
        c[j] = fg * c[j] + ig * gg; h[j] = og * Math.tanh(c[j]);
      }
      inp = h;
    }
    var z = this.z;
    for (r = 0; r < H; r++) { s = this.b1[r]; for (k = 0; k < H; k++) s += this.W1[r * H + k] * inp[k]; z[r] = Math.tanh(s); }
    for (r = 0; r < this.nOut; r++) { s = this.b2[r]; for (k = 0; k < H; k++) s += this.W2[r * H + k] * z[k]; out[r] = s; }
  };

  function Twin(D) {
    this.D = D; this.nIn = D.inputs.length; this.nOut = D.targets.length;
    var self = this;
    this.members = D.weights.map(function (w) { return new Member(decode(w), self.nIn, D.hidden, D.layers, self.nOut); });
    this.nParams = decode(D.weights[0]).length;
    this.xs = new Float64Array(this.nIn); this.tmp = new Float64Array(this.nOut);
  }
  /* Reset to rest and run the warm-up (plant at steady state with inputs u before t = 0). */
  Twin.prototype.reset = function (u) {
    this.members.forEach(function (m) { m.reset(); });
    var r; for (var i = 0; i < this.D.warmup; i++) r = this.step(u);
    return r;
  };
  /* One 60 s step. Returns physical-unit mean, min and max across ensemble members. */
  Twin.prototype.step = function (u) {
    var D = this.D, n = this.nOut, mean = new Float64Array(n), lo = new Float64Array(n).fill(Infinity),
        hi = new Float64Array(n).fill(-Infinity);
    for (var k = 0; k < this.nIn; k++) this.xs[k] = (u[k] - D.x_mean[k]) / D.x_std[k];
    for (var m = 0; m < this.members.length; m++) {
      this.members[m].step(this.xs, this.tmp);
      for (var j = 0; j < n; j++) {
        var v = this.tmp[j] * D.y_std[j] + D.y_mean[j];
        mean[j] += v / this.members.length; if (v < lo[j]) lo[j] = v; if (v > hi[j]) hi[j] = v;
      }
    }
    return { mean: mean, lo: lo, hi: hi };
  };
  return { Twin: Twin };
})();
if (typeof module !== 'undefined') module.exports = TwinEngine;
