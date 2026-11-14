// NEURAL HORIZON — render engine: helpers, characters, backgrounds, HUD,
// subtitles, transitions. Scene renderers live in scenes.js.
'use strict';
const W = 1920, H = 1080;
const TL = window.TIMELINE;
const cv = document.getElementById('c');
const ctx = cv.getContext('2d');

// chapter accents (0 = prologue) and deep background pairs
const ACC = ['#7fe7ff', '#4de8ff', '#a68bff', '#ffb547', '#3df5b0', '#ff5fa2', '#ff8a5c', '#7ab8ff', '#ffd27a'];
const BGC = [
  ['#05070f', '#0b1426'], ['#040b14', '#08263a'], ['#07051a', '#1a1240'], ['#0d0806', '#2a1a08'],
  ['#03100c', '#06302a'], ['#0f0510', '#2c0c2a'], ['#0f0806', '#2e130c'], ['#050a14', '#0d2140'], ['#0a0806', '#2a1f10'],
];
const GOOD = '#3df5b0', BAD = '#ff5470', WARN = '#ffb547', TXT = '#eef3ff', DIM = '#8b97b5';
const F = { ui: 'Inter', head: '"Space Grotesk"', mono: '"JetBrains Mono"' };

// ------------------------------------------------------------------ math
const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const lerp = (a, b, p) => a + (b - a) * p;
const P = (t, a, b) => clamp((t - a) / (b - a));
const E = {
  io: p => p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2,
  out: p => 1 - Math.pow(1 - p, 3),
  expo: p => p === 1 ? 1 : 1 - Math.pow(2, -10 * p),
  back: p => { const c = 1.70158; return 1 + (c + 1) * Math.pow(p - 1, 3) + c * Math.pow(p - 1, 2); },
  in: p => p * p * p,
};
function hash(i) { const x = Math.sin(i * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); }
function hexA(hex, a) {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${n >> 16},${(n >> 8) & 255},${n & 255},${a})`;
}
function mix(h1, h2, p) {
  const a = parseInt(h1.slice(1), 16), b = parseInt(h2.slice(1), 16);
  const r = Math.round(lerp(a >> 16, b >> 16, p)), g = Math.round(lerp((a >> 8) & 255, (b >> 8) & 255, p)), bl = Math.round(lerp(a & 255, b & 255, p));
  return '#' + ((1 << 24) + (r << 16) + (g << 8) + bl).toString(16).slice(1);
}
const fmt = n => Math.round(n).toLocaleString('en-US');

// ------------------------------------------------------------------ draw primitives
function rr(c, x, y, w, h, r) {
  r = Math.min(r, w / 2, h / 2);
  c.beginPath(); c.moveTo(x + r, y); c.arcTo(x + w, y, x + w, y + h, r); c.arcTo(x + w, y + h, x, y + h, r);
  c.arcTo(x, y + h, x, y, r); c.arcTo(x, y, x + w, y, r); c.closePath();
}
function glass(c, x, y, w, h, o = {}) {
  const r = o.r ?? 22, acc = o.acc || '#9fdcff', a = o.a ?? 1;
  if (a <= 0) return;
  c.save(); c.globalAlpha *= a;
  // drop shadow
  c.fillStyle = 'rgba(0,0,0,0.35)'; rr(c, x + 6, y + 14, w, h, r); c.fill();
  const g = c.createLinearGradient(x, y, x + w * .4, y + h);
  g.addColorStop(0, `rgba(255,255,255,${o.fill ?? 0.11})`); g.addColorStop(1, `rgba(255,255,255,${(o.fill ?? 0.11) * 0.35})`);
  rr(c, x, y, w, h, r); c.fillStyle = 'rgba(8,12,24,0.55)'; c.fill(); c.fillStyle = g; c.fill();
  // tinted inner glow
  const g2 = c.createRadialGradient(x + w * .2, y, 0, x + w * .2, y, Math.max(w, h));
  g2.addColorStop(0, hexA(acc, 0.13)); g2.addColorStop(1, hexA(acc, 0));
  c.fillStyle = g2; c.fill();
  // border with highlight
  const b = c.createLinearGradient(x, y, x + w, y + h);
  b.addColorStop(0, hexA(acc, o.stroke ?? 0.55)); b.addColorStop(.5, 'rgba(255,255,255,0.10)'); b.addColorStop(1, hexA(acc, (o.stroke ?? .55) * .5));
  c.strokeStyle = b; c.lineWidth = o.lw ?? 1.5; c.stroke();
  // top shine
  c.beginPath(); c.moveTo(x + r, y + 1.5); c.lineTo(x + w - r, y + 1.5);
  c.strokeStyle = 'rgba(255,255,255,0.28)'; c.lineWidth = 1; c.stroke();
  c.restore();
}
function txt(c, s, x, y, o = {}) {
  const a = o.a ?? 1; if (a <= 0) return;
  c.save(); c.globalAlpha *= a;
  c.font = `${o.w || 500} ${o.size || 28}px ${o.f || F.ui}`;
  c.letterSpacing = (o.ls || 0) + 'px';
  c.textAlign = o.align || 'left'; c.textBaseline = o.base || 'alphabetic';
  if (o.glow) { c.shadowColor = o.glowColor || o.color || '#fff'; c.shadowBlur = o.glow; }
  if (o.stroke) { c.strokeStyle = o.stroke; c.lineWidth = o.lw || 2; c.strokeText(s, x, y); }
  else { c.fillStyle = o.color || TXT; c.fillText(s, x, y); }
  c.restore();
}
function measure(c, s, o = {}) {
  c.save(); c.font = `${o.w || 500} ${o.size || 28}px ${o.f || F.ui}`; c.letterSpacing = (o.ls || 0) + 'px';
  const m = c.measureText(s).width; c.restore(); return m;
}
function wrap(c, s, maxW, o) {
  const words = s.split(' '); const lines = []; let cur = '';
  for (const w of words) {
    const t = cur ? cur + ' ' + w : w;
    if (measure(c, t, o) > maxW && cur) { lines.push(cur); cur = w; } else cur = t;
  }
  if (cur) lines.push(cur); return lines;
}
function para(c, s, x, y, maxW, o = {}) {
  const ls = wrap(c, s, maxW, o); const lh = o.lh || (o.size || 28) * 1.35;
  ls.forEach((l, i) => txt(c, l, x, y + i * lh, o)); return ls.length * lh;
}
// kinetic per-character reveal
function kinetic(c, s, x, y, p, o = {}) {
  const n = s.length; const tw = measure(c, s, o);
  let cx = o.align === 'center' ? x - tw / 2 : o.align === 'right' ? x - tw : x;
  for (let i = 0; i < n; i++) {
    const q = E.out(clamp(p * (1 + n * 0.06) - i * 0.06));
    const ch = s[i]; const cw = measure(c, ch, o) + (o.ls || 0) * 0;
    if (q > 0) txt(c, ch, cx, y + (1 - q) * (o.rise ?? 40), { ...o, align: 'left', a: (o.a ?? 1) * q });
    cx += measure(c, s.slice(0, i + 1), o) - measure(c, s.slice(0, i), o);
  }
}
function scramble(s, p, seed = 1) {
  const pool = '01#$%&*+<>/\\=ABCDEFGHJKLMNPQRSTUVWXYZ';
  let out = '';
  for (let i = 0; i < s.length; i++) {
    const th = i / s.length * 0.8;
    if (s[i] === ' ') out += ' ';
    else if (p > th + 0.15) out += s[i];
    else if (p > th - 0.2) out += pool[Math.floor(hash(i * 7 + seed + Math.floor(p * 40)) * pool.length)];
    else out += ' ';
  }
  return out;
}
const typed = (s, p) => s.slice(0, Math.round(s.length * clamp(p)));
function glowDot(c, x, y, r, col, a = 1) {
  if (a <= 0 || r <= 0) return;
  const g = c.createRadialGradient(x, y, 0, x, y, r);
  g.addColorStop(0, hexA(col, a)); g.addColorStop(.25, hexA(col, a * .45)); g.addColorStop(1, hexA(col, 0));
  c.fillStyle = g; c.fillRect(x - r, y - r, r * 2, r * 2);
}
function glowLine(c, pts, col, a = 1, w = 2) {
  if (a <= 0) return;
  c.save(); c.lineCap = 'round'; c.lineJoin = 'round';
  for (const [lw, al] of [[w * 6, .08], [w * 2.5, .22], [w, 1]]) {
    c.beginPath(); pts.forEach((p, i) => i ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1]));
    c.strokeStyle = hexA(col, al * a); c.lineWidth = lw; c.stroke();
  }
  c.restore();
}
// animated flow along a straight segment: line draw-on + travelling pulses
function flow(c, x1, y1, x2, y2, t, p, col, o = {}) {
  if (p <= 0) return;
  const xe = lerp(x1, x2, p), ye = lerp(y1, y2, p);
  glowLine(c, [[x1, y1], [xe, ye]], col, (o.a ?? 1) * .55, o.w || 2);
  if (p >= 1) {
    for (let k = 0; k < (o.n || 3); k++) {
      const q = ((t * (o.speed || .7)) + k / (o.n || 3)) % 1;
      glowDot(c, lerp(x1, x2, q), lerp(y1, y2, q), 14, col, (o.a ?? 1) * .9);
    }
    if (o.arrow !== false) arrowHead(c, x2, y2, Math.atan2(y2 - y1, x2 - x1), col, o.a ?? 1);
  }
}
function arrowHead(c, x, y, ang, col, a = 1) {
  c.save(); c.translate(x, y); c.rotate(ang); c.globalAlpha *= a;
  c.beginPath(); c.moveTo(0, 0); c.lineTo(-14, -8); c.lineTo(-14, 8); c.closePath(); c.fillStyle = col; c.fill(); c.restore();
}
function pill(c, s, x, y, col, o = {}) {
  const size = o.size || 20; const pad = o.pad ?? 16;
  const w = measure(c, s, { size, w: o.w || 600, ls: o.ls ?? 1.5, f: o.f }) + pad * 2; const h = size * 1.9;
  const x0 = o.align === 'center' ? x - w / 2 : o.align === 'right' ? x - w : x;
  const a = o.a ?? 1; if (a <= 0) return w;
  c.save(); c.globalAlpha *= a;
  rr(c, x0, y - h / 2, w, h, h / 2); c.fillStyle = o.solid ? col : 'rgba(8,12,24,0.72)'; c.fill();
  if (!o.solid) { c.fillStyle = hexA(col, .14); c.fill(); c.strokeStyle = hexA(col, .8); c.lineWidth = 1.5; c.stroke(); }
  c.restore();
  txt(c, s, x0 + pad, y + size * .36, { size, w: o.w || 600, color: o.solid ? '#06101c' : (o.tc || TXT), ls: o.ls ?? 1.5, a, f: o.f });
  return w;
}
// motion-tracked label: dot at anchor + leader + pill
function tag(c, ax, ay, x, y, s, col, a = 1, o = {}) {
  if (a <= 0) return;
  const p = E.out(clamp(a));
  glowDot(c, ax, ay, 16, col, p);
  c.save(); c.globalAlpha *= p; c.fillStyle = col; c.beginPath(); c.arc(ax, ay, 4, 0, 7); c.fill();
  c.strokeStyle = hexA(col, .8); c.lineWidth = 1.5; c.beginPath(); c.moveTo(ax, ay);
  const mx = lerp(ax, x, p), my = lerp(ay, y, p); c.lineTo(mx, ay + (my - ay)); c.stroke(); c.restore();
  pill(c, s, x + (x > ax ? 6 : -6), y, col, { a: P(a, .4, 1), align: x > ax ? 'left' : 'right', size: o.size || 18 });
}
function bar(c, x, y, w, h, p, col, o = {}) {
  rr(c, x, y, w, h, h / 2); c.fillStyle = o.bg || 'rgba(255,255,255,0.08)'; c.fill();
  if (p > 0) {
    rr(c, x, y, Math.max(h, w * p), h, h / 2);
    const g = c.createLinearGradient(x, 0, x + w, 0); g.addColorStop(0, hexA(col, .6)); g.addColorStop(1, col);
    c.fillStyle = g; c.fill(); glowDot(c, x + w * p, y + h / 2, h * 2.2, col, .6);
  }
}
function ring(c, x, y, r, p, col, w = 6, a = 1) {
  c.save(); c.globalAlpha *= a; c.lineCap = 'round';
  c.beginPath(); c.arc(x, y, r, 0, 7); c.strokeStyle = 'rgba(255,255,255,0.08)'; c.lineWidth = w; c.stroke();
  c.beginPath(); c.arc(x, y, r, -Math.PI / 2, -Math.PI / 2 + p * Math.PI * 2); c.strokeStyle = col; c.stroke();
  c.restore();
}
function check(c, x, y, s, col, p = 1) {
  c.save(); c.lineCap = 'round'; c.lineJoin = 'round'; c.strokeStyle = col; c.lineWidth = s * .16;
  const pts = [[-.35, 0], [-.1, .28], [.4, -.3]];
  const L1 = .35, q = clamp(p);
  c.beginPath(); c.moveTo(x + pts[0][0] * s, y + pts[0][1] * s);
  if (q < L1) c.lineTo(x + lerp(pts[0][0], pts[1][0], q / L1) * s, y + lerp(pts[0][1], pts[1][1], q / L1) * s);
  else { c.lineTo(x + pts[1][0] * s, y + pts[1][1] * s); const r = (q - L1) / (1 - L1); c.lineTo(x + lerp(pts[1][0], pts[2][0], r) * s, y + lerp(pts[1][1], pts[2][1], r) * s); }
  c.stroke(); c.restore();
}
function cross(c, x, y, s, col, a = 1) {
  c.save(); c.globalAlpha *= a; c.strokeStyle = col; c.lineCap = 'round'; c.lineWidth = s * .16;
  c.beginPath(); c.moveTo(x - s * .3, y - s * .3); c.lineTo(x + s * .3, y + s * .3); c.moveTo(x + s * .3, y - s * .3); c.lineTo(x - s * .3, y + s * .3); c.stroke(); c.restore();
}
// 3D projection
function proj(x, y, z, cam) {
  const cy = Math.cos(cam.yaw || 0), sy = Math.sin(cam.yaw || 0), cp = Math.cos(cam.pitch || 0), sp = Math.sin(cam.pitch || 0);
  let X = x * cy - z * sy, Z = x * sy + z * cy;
  let Y = y * cp - Z * sp; Z = y * sp + Z * cp;
  Z += cam.dist || 1200;
  const f = (cam.f || 1000) / Math.max(1, Z);
  return [(cam.cx ?? W / 2) + X * f, (cam.cy ?? H / 2) + Y * f, f, Z];
}
// isometric projection
const ISO = { c: Math.cos(Math.PI / 6), s: Math.sin(Math.PI / 6) };
function iso(x, y, z, o) { return [o.cx + (x - y) * ISO.c * o.k, o.cy + (x + y) * ISO.s * o.k - z * o.k]; }
function isoBox(c, x, y, z, w, d, h, o, cols, a = 1) {
  const p = (X, Y, Z) => iso(X, Y, Z, o);
  c.save(); c.globalAlpha *= a;
  const face = (pts, col) => { c.beginPath(); pts.forEach((q, i) => i ? c.lineTo(q[0], q[1]) : c.moveTo(q[0], q[1])); c.closePath(); c.fillStyle = col; c.fill(); };
  face([p(x, y + d, z), p(x + w, y + d, z), p(x + w, y + d, z + h), p(x, y + d, z + h)], cols[1]);
  face([p(x + w, y, z), p(x + w, y + d, z), p(x + w, y + d, z + h), p(x + w, y, z + h)], cols[2]);
  face([p(x, y, z + h), p(x + w, y, z + h), p(x + w, y + d, z + h), p(x, y + d, z + h)], cols[0]);
  c.restore();
}

// ------------------------------------------------------------------ characters
const PEOPLE = {
  NOVA: { skin: '#c68863', hair: '#1c1630', top: '#13516a', top2: '#0a2e40', acc: '#4de8ff', style: 'bob', pants: '#141a2e' },
  ARJUN: { skin: '#a86f4c', hair: '#121212', top: '#2b3a66', top2: '#18213e', acc: '#ffb547', style: 'short', glasses: true, pants: '#1b1f2c' },
  LIN: { skin: '#f0c9a8', hair: '#2a1a14', top: '#e9eef6', top2: '#b7c3d6', acc: '#3df5b0', style: 'long', pants: '#2a2f45', coat: true },
  KAI: { skin: '#7a4a32', hair: '#0d0d12', top: '#56307a', top2: '#2e1745', acc: '#ff5fa2', style: 'spiky', headset: true, pants: '#1a1426' },
  MAYA: { skin: '#e0ae86', hair: '#5a2e1a', top: '#ff8a5c', top2: '#b4512c', acc: '#ff8a5c', style: 'bun', apron: true, pants: '#3a2a26' },
  SAM: { skin: '#d9a27c', hair: '#3a2a1a', top: '#2a6b4a', top2: '#173d2b', acc: '#3df5b0', style: 'cap', cap: '#2fbf71', pants: '#22283a', phone: true },
};
const STAGE_COL = ['#7fe7ff', '#a68bff', '#3df5b0', '#ff8a5c', '#ffd27a'];

// x,y = feet; s = scale (1 => ~430px tall). o: {amp, look, t, a, silhouette, wave}
function person(c, who, x, y, s, o = {}) {
  const P_ = PEOPLE[who]; const t = o.t || 0; const a = o.a ?? 1; if (a <= 0) return;
  const look = o.look || 0, amp = clamp(o.amp || 0);
  const breathe = Math.sin(t * 2.1 + x) * 2.5;
  c.save(); c.globalAlpha *= a; c.translate(x, y); c.scale(s, s);
  const sil = o.silhouette;
  const col = k => sil ? '#05070d' : P_[k];
  // floor glow + shadow
  if (!sil) { glowDot(c, 0, 0, 170, P_.acc, .18); }
  c.fillStyle = 'rgba(0,0,0,0.45)'; c.beginPath(); c.ellipse(0, 0, 95, 16, 0, 0, 7); c.fill();
  // legs
  c.fillStyle = col('pants'); rr(c, -46, -150, 40, 150, 16); c.fill(); rr(c, 6, -150, 40, 150, 16); c.fill();
  c.fillStyle = sil ? '#05070d' : '#0c0f18'; rr(c, -52, -18, 50, 20, 9); c.fill(); rr(c, 4, -18, 50, 20, 9); c.fill();
  // arms (behind torso edges)
  const sw = Math.sin(t * 1.6 + x * .01) * 0.05 + (amp > .15 ? Math.sin(t * 7) * .04 : 0);
  for (const sd of [-1, 1]) {
    c.save(); c.translate(sd * 70, -280 + breathe); c.rotate(sd * (0.12 + sw * sd) + (o.wave && sd === 1 ? -2.4 + Math.sin(t * 8) * .3 : 0));
    c.fillStyle = col('top2'); rr(c, -19, 0, 38, 150, 19); c.fill();
    c.fillStyle = col('skin'); c.beginPath(); c.arc(0, 152, 18, 0, 7); c.fill(); c.restore();
  }
  // torso
  c.save(); c.translate(0, breathe);
  c.beginPath(); c.moveTo(-78, -270); c.quadraticCurveTo(0, -292, 78, -270); c.lineTo(62, -140); c.quadraticCurveTo(0, -128, -62, -140); c.closePath();
  if (sil) c.fillStyle = '#05070d'; else { const g = c.createLinearGradient(-80, -290, 80, -130); g.addColorStop(0, P_.top); g.addColorStop(1, P_.top2); c.fillStyle = g; }
  c.fill();
  // rim light
  c.strokeStyle = hexA(P_.acc, sil ? .9 : .55); c.lineWidth = sil ? 4 : 3; c.stroke();
  if (!sil) {
    if (P_.coat) { c.strokeStyle = '#9aa7bd'; c.lineWidth = 3; c.beginPath(); c.moveTo(0, -282); c.lineTo(0, -134); c.stroke(); c.fillStyle = '#3df5b0'; rr(c, 22, -240, 26, 6, 3); c.fill(); }
    if (P_.apron) { c.fillStyle = '#f6e7d8'; rr(c, -46, -226, 92, 100, 14); c.fill(); c.fillStyle = '#e7cdb5'; rr(c, -20, -196, 40, 24, 6); c.fill(); }
    if (who === 'NOVA') { // hoodie strings + stage badge
      c.strokeStyle = '#7fd8ef'; c.lineWidth = 3; c.beginPath(); c.moveTo(-14, -262); c.lineTo(-16, -222); c.moveTo(14, -262); c.lineTo(16, -222); c.stroke();
      const sc = STAGE_COL[o.stage ?? 0]; glowDot(c, 40, -232, 26, sc, .9); c.fillStyle = sc; c.beginPath(); c.arc(40, -232, 7, 0, 7); c.fill();
    }
    if (who === 'ARJUN') { c.fillStyle = '#ffb547'; rr(c, -40, -250, 22, 6, 3); c.fill(); }
  }
  // neck + head
  c.fillStyle = col('skin'); rr(c, -16, -300, 32, 36, 10); c.fill();
  const hy = -352; const hx = look * 6;
  // hair back layer
  if (!sil) {
    c.fillStyle = P_.hair;
    if (P_.style === 'long') { rr(c, -66 + hx, hy - 50, 132, 150, 50); c.fill(); }
    if (P_.style === 'bob') { rr(c, -70 + hx, hy - 54, 140, 112, 46); c.fill(); }
  }
  let g;
  if (sil) c.fillStyle = '#05070d';
  else { g = c.createRadialGradient(hx - 18, hy - 22, 6, hx, hy, 70); g.addColorStop(0, mix(P_.skin, '#ffffff', .18)); g.addColorStop(1, mix(P_.skin, '#000000', .18)); c.fillStyle = g; }
  c.beginPath(); c.ellipse(hx, hy, 56, 62, 0, 0, 7); c.fill();
  if (sil) { c.strokeStyle = hexA(P_.acc, .9); c.lineWidth = 4; c.stroke(); c.restore(); c.restore(); return; }
  // hair front
  c.fillStyle = P_.hair;
  c.beginPath();
  switch (P_.style) {
    case 'bob':
      c.ellipse(hx, hy - 30, 62, 40, 0, Math.PI, 0); c.fill();
      c.beginPath(); c.moveTo(hx - 62, hy - 30); c.quadraticCurveTo(hx - 10, hy - 10, hx + 20, hy - 46); c.lineTo(hx + 62, hy - 30); c.lineTo(hx + 62, hy - 60); c.lineTo(hx - 62, hy - 60); c.fill();
      c.strokeStyle = '#4de8ff'; c.lineWidth = 7; c.lineCap = 'round'; c.beginPath(); c.moveTo(hx + 30, hy - 58); c.quadraticCurveTo(hx + 58, hy - 30, hx + 60, hy + 30); c.stroke();
      break;
    case 'short': c.ellipse(hx, hy - 34, 58, 34, 0, Math.PI, 0); c.fill(); break;
    case 'long': c.ellipse(hx, hy - 30, 60, 40, 0, Math.PI, 0); c.fill(); c.beginPath(); c.moveTo(hx - 58, hy - 30); c.quadraticCurveTo(hx, hy - 20, hx + 4, hy - 64); c.lineTo(hx - 58, hy - 60); c.fill(); break;
    case 'spiky':
      c.moveTo(hx - 56, hy - 20);
      for (let i = 0; i <= 6; i++) { const xx = hx - 56 + i * 18.6; c.lineTo(xx + 6, hy - 78 + (i % 2) * 18); c.lineTo(xx + 14, hy - 40); }
      c.lineTo(hx + 56, hy - 20); c.closePath(); c.fill(); break;
    case 'bun': c.ellipse(hx, hy - 34, 60, 34, 0, Math.PI, 0); c.fill(); c.beginPath(); c.arc(hx, hy - 82, 26, 0, 7); c.fill(); break;
    case 'cap':
      c.fillStyle = P_.cap; c.ellipse(hx, hy - 30, 60, 40, 0, Math.PI, 0); c.fill();
      c.beginPath(); c.ellipse(hx + 40 * (look >= 0 ? 1 : -1), hy - 30, 44, 9, 0, 0, 7); c.fill(); break;
  }
  // eyes (blink)
  const bl = (t + hash(x) * 4) % 3.9 < 0.12 ? .15 : 1;
  c.fillStyle = '#121626';
  for (const sd of [-1, 1]) { c.beginPath(); c.ellipse(hx + sd * 21 + look * 7, hy - 4, 6.5, 8 * bl, 0, 0, 7); c.fill(); }
  c.fillStyle = 'rgba(255,255,255,0.8)'; for (const sd of [-1, 1]) { c.beginPath(); c.arc(hx + sd * 21 + look * 7 + 2, hy - 7, 2, 0, 7); c.fill(); }
  // brows
  c.strokeStyle = mix(P_.hair, '#000', .2); c.lineWidth = 4; c.lineCap = 'round';
  for (const sd of [-1, 1]) { c.beginPath(); c.moveTo(hx + sd * 12 + look * 6, hy - 22 - amp * 3); c.lineTo(hx + sd * 30 + look * 6, hy - 24 - amp * 3); c.stroke(); }
  // mouth
  const mx = hx + look * 6, my = hy + 26;
  if (amp > 0.06) { c.fillStyle = '#5a1f2a'; c.beginPath(); c.ellipse(mx, my, 11 + amp * 3, 2 + amp * 11, 0, 0, 7); c.fill(); }
  else { c.strokeStyle = '#5a1f2a'; c.lineWidth = 3.5; c.beginPath(); c.arc(mx, my - 8, 12, 0.35 * Math.PI, 0.65 * Math.PI); c.stroke(); }
  // cheeks
  glowDot(c, hx - 34, hy + 12, 16, '#ff7a8a', .18); glowDot(c, hx + 34, hy + 12, 16, '#ff7a8a', .18);
  if (P_.glasses) { c.strokeStyle = '#e8edf5'; c.lineWidth = 3; for (const sd of [-1, 1]) { rr(c, hx + sd * 21 - 15 + look * 7, hy - 16, 30, 22, 7); c.stroke(); } c.beginPath(); c.moveTo(hx - 6 + look * 7, hy - 6); c.lineTo(hx + 6 + look * 7, hy - 6); c.stroke(); }
  if (P_.headset) { c.strokeStyle = '#ff5fa2'; c.lineWidth = 6; c.beginPath(); c.arc(hx, hy - 6, 62, Math.PI * 1.05, Math.PI * 1.95); c.stroke(); c.fillStyle = '#ff5fa2'; rr(c, hx - 70, hy - 18, 16, 34, 6); c.fill(); c.lineWidth = 3; c.beginPath(); c.moveTo(hx - 62, hy + 12); c.quadraticCurveTo(hx - 50, hy + 40, hx - 18, hy + 34); c.stroke(); }
  c.restore(); // breathe
  // props
  if (P_.phone || o.tablet) { c.fillStyle = '#0a0d16'; rr(c, 52, -150 + breathe, 34, 58, 7); c.fill(); c.fillStyle = hexA(P_.acc, .8); rr(c, 56, -145 + breathe, 26, 46, 4); c.fill(); }
  c.restore();
}
// bust portrait in a circular frame (video-call style)
function bust(c, who, x, y, r, o = {}) {
  const a = o.a ?? 1; if (a <= 0) return;
  c.save(); c.globalAlpha *= a;
  c.beginPath(); c.arc(x, y, r, 0, 7); c.fillStyle = 'rgba(8,12,24,0.85)'; c.fill();
  c.save(); c.clip(); glowDot(c, x, y + r * .2, r * 1.3, PEOPLE[who].acc, .25);
  person(c, who, x, y + r * 2.25, r / 125, { ...o, a: 1 }); c.restore();
  c.strokeStyle = hexA(PEOPLE[who].acc, .9); c.lineWidth = 3; c.beginPath(); c.arc(x, y, r, 0, 7); c.stroke();
  if (o.amp > .08) { c.strokeStyle = hexA(PEOPLE[who].acc, .35 * o.amp); c.lineWidth = 2; c.beginPath(); c.arc(x, y, r + 8 + o.amp * 8, 0, 7); c.stroke(); }
  c.restore();
}
// AI agent bot
function bot(c, x, y, s, col, o = {}) {
  const t = o.t || 0, a = o.a ?? 1; if (a <= 0) return;
  const bob = Math.sin(t * 2.4 + x * .03) * 6;
  c.save(); c.globalAlpha *= a; c.translate(x, y); c.scale(s, s);
  c.fillStyle = 'rgba(0,0,0,0.4)'; c.beginPath(); c.ellipse(0, 0, 50, 12, 0, 0, 7); c.fill();
  glowDot(c, 0, 0, 90, col, .25 + (o.active ? .3 : 0));
  c.translate(0, -30 + bob);
  // body
  const g = c.createLinearGradient(-50, -150, 50, 0); g.addColorStop(0, '#2a3350'); g.addColorStop(1, '#0f1424');
  rr(c, -46, -110, 92, 100, 34); c.fillStyle = g; c.fill(); c.strokeStyle = hexA(col, .8); c.lineWidth = 2.5; c.stroke();
  // head
  rr(c, -54, -190, 108, 78, 30); c.fillStyle = g; c.fill(); c.stroke();
  rr(c, -42, -178, 84, 54, 20); c.fillStyle = '#060a14'; c.fill();
  // face
  const bl = (t + x * .01) % 3.1 < .1 ? .2 : 1;
  c.fillStyle = col; for (const sd of [-1, 1]) { rr(c, sd * 18 - 7, -160 - 9 * bl, 14, 18 * bl, 6); c.fill(); }
  glowDot(c, -18, -160, 20, col, .6); glowDot(c, 18, -160, 20, col, .6);
  if (o.active) { c.strokeStyle = col; c.lineWidth = 3; c.beginPath(); c.arc(0, -142, 8, 0.1 * Math.PI, 0.9 * Math.PI); c.stroke(); }
  // antenna
  c.strokeStyle = hexA(col, .8); c.lineWidth = 3; c.beginPath(); c.moveTo(0, -190); c.lineTo(0, -214); c.stroke();
  glowDot(c, 0, -218, 18, col, .9 * (0.6 + 0.4 * Math.sin(t * 5 + x))); c.fillStyle = col; c.beginPath(); c.arc(0, -218, 5, 0, 7); c.fill();
  // chest light
  c.fillStyle = hexA(col, .9); rr(c, -16, -70, 32, 8, 4); c.fill();
  c.restore();
}

// ------------------------------------------------------------------ background + post
const DUST = Array.from({ length: 220 }, (_, i) => ({ x: hash(i) * 2400 - 240, y: hash(i + 99) * H, z: .2 + hash(i + 7) * .8, r: .6 + hash(i + 3) * 1.8 }));
function background(c, ch, t, camX = 0) {
  const [a, b] = BGC[ch];
  const g = c.createRadialGradient(W * .5, H * .38, 50, W * .5, H * .5, W * .8);
  g.addColorStop(0, b); g.addColorStop(1, a); c.fillStyle = g; c.fillRect(0, 0, W, H);
  // drifting light fog
  c.save(); c.globalCompositeOperation = 'lighter';
  for (let i = 0; i < 3; i++) {
    const x = W * (.2 + .3 * i) + Math.sin(t * .13 + i * 2) * 220 - camX * .05, y = H * (.3 + .2 * (i % 2)) + Math.cos(t * .11 + i) * 120;
    glowDot(c, x, y, 620, i === 1 ? ACC[ch] : mix(ACC[ch], '#5a6cff', .5), .07);
  }
  // dust parallax
  for (const d of DUST) {
    const x = ((d.x - camX * d.z * .35 + t * 8 * d.z) % 2400 + 2400) % 2400 - 240, y = (d.y - t * 5 * d.z + H) % H;
    c.fillStyle = hexA(ACC[ch], .18 * d.z); c.fillRect(x, y, d.r * d.z * 1.6, d.r * d.z * 1.6);
  }
  c.restore();
}
let GRAIN = [];
function makeGrain() {
  for (let k = 0; k < 4; k++) {
    const g = document.createElement('canvas'); g.width = g.height = 256; const gc = g.getContext('2d');
    const im = gc.createImageData(256, 256);
    for (let i = 0; i < im.data.length; i += 4) { const v = (hash(i * .37 + k * 1000) * 255) | 0; im.data[i] = im.data[i + 1] = im.data[i + 2] = v; im.data[i + 3] = 14; }
    gc.putImageData(im, 0, 0); GRAIN.push(g);
  }
}
let VIG;
function makeVignette() {
  VIG = document.createElement('canvas'); VIG.width = W; VIG.height = H; const v = VIG.getContext('2d');
  const g = v.createRadialGradient(W / 2, H / 2, H * .35, W / 2, H / 2, W * .72);
  g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(0,0,0,0.72)'); v.fillStyle = g; v.fillRect(0, 0, W, H);
}
function post(c, frame) {
  c.drawImage(VIG, 0, 0);
  const g = GRAIN[frame % 4]; const ox = (hash(frame) * 256) | 0, oy = (hash(frame + 5) * 256) | 0;
  c.save(); c.globalCompositeOperation = 'overlay';
  for (let x = -ox; x < W; x += 256) for (let y = -oy; y < H; y += 256) c.drawImage(g, x, y);
  c.restore();
}

// ------------------------------------------------------------------ HUD + subtitles
const NO_HUD = new Set(['cold_open', 'title', 'end']);
function stageAt(sc, t) {
  if (sc.type === 'horizon') { const L = sc.lines; return t >= L[3].s + 3.2 ? 4 : 3; }
  if (sc.type === 'end') return 4;
  return TL.ch_stage[sc.ch];
}
function hud(c, sc, t, gt) {
  let a = NO_HUD.has(sc.type) ? 0 : 1;
  const prev = TL.scenes[sc.i - 1], next = TL.scenes[sc.i + 1];
  if (!a && next && !NO_HUD.has(next.type)) a = P(t, sc.dur - .6, sc.dur);
  if (a && prev && NO_HUD.has(prev.type)) a = Math.min(a, P(t, 0, .8));
  if (sc.type === 'chapter') a *= .0 + P(t, sc.dur - .8, sc.dur);
  if (a <= 0) return;
  const ch = sc.ch, acc = ACC[ch];
  c.save(); c.globalAlpha = a;
  // chapter label
  txt(c, `CHAPTER ${String(ch).padStart(2, '0')} / 08`, 70, 72, { size: 15, w: 600, ls: 4, color: acc, f: F.mono });
  txt(c, TL.chapters[ch][0].toUpperCase(), 70, 104, { size: 24, w: 700, ls: 3, f: F.head });
  // progress segments
  const x0 = 70, y0 = 124, sw = 44;
  const tot = TL.duration;
  for (let i = 1; i <= 8; i++) {
    const x = x0 + (i - 1) * (sw + 6);
    c.fillStyle = 'rgba(255,255,255,0.14)'; rr(c, x, y0, sw, 4, 2); c.fill();
    let fill = i < ch ? 1 : i > ch ? 0 : 0;
    if (i === ch) { const chs = TL.scenes.filter(s => s.ch === ch); const s0 = chs[0].start, s1 = chs[chs.length - 1].start + chs[chs.length - 1].dur; fill = clamp((gt - s0) / (s1 - s0)); }
    if (fill > 0) { c.fillStyle = i === ch ? acc : hexA(ACC[i], .75); rr(c, x, y0, sw * fill, 4, 2); c.fill(); }
  }
  // Nova stage badge (top right)
  const st = stageAt(sc, t); const sc_ = STAGE_COL[st];
  const bx = W - 70;
  bust(c, 'NOVA', bx - 30, 92, 30, { t: gt, stage: st });
  txt(c, 'NOVA · STAGE ' + (st + 1) + '/5', bx - 76, 84, { size: 13, w: 600, ls: 3, color: DIM, align: 'right', f: F.mono });
  txt(c, TL.stages[st].toUpperCase(), bx - 76, 112, { size: 21, w: 700, ls: 2, color: sc_, align: 'right', f: F.head });
  for (let i = 0; i < 5; i++) { c.fillStyle = i <= st ? STAGE_COL[i] : 'rgba(255,255,255,0.15)'; rr(c, bx - 76 - (4 - i) * 22 - 16, 126, 16, 4, 2); c.fill(); }
  c.restore();
}
function subtitles(c, sc, t) {
  for (const L of sc.lines) {
    if (t < L.s - .15 || t > L.e + .35) continue;
    const a = Math.min(P(t, L.s - .15, L.s + .1), 1 - P(t, L.e + .1, L.e + .35));
    const spk = TL.speakers[L.who]; const isN = L.who === 'N';
    const o = { size: 33, w: 500 }; const lines = wrap(c, L.text, 1250, o);
    const lh = 44, h = lines.length * lh + (isN ? 30 : 64); const y = H - 66 - h;
    let maxw = 0; lines.forEach(l => maxw = Math.max(maxw, measure(c, l, o)));
    const w = Math.max(maxw, isN ? 0 : 300) + 72; const x = W / 2 - w / 2;
    c.save(); c.globalAlpha = a;
    rr(c, x, y, w, h, 18); c.fillStyle = 'rgba(4,7,15,0.62)'; c.fill();
    const col = isN ? '#ffffff' : PEOPLE[L.who].acc;
    c.strokeStyle = hexA(col, isN ? .12 : .45); c.lineWidth = 1.2; c.stroke();
    let yy = y + 50;
    if (!isN) { txt(c, spk.name.toUpperCase() + '  ·  ' + spk.role.toUpperCase(), W / 2, y + 38, { size: 15, w: 700, ls: 3, color: col, align: 'center', f: F.mono }); yy += 32; }
    lines.forEach((l, i) => txt(c, l, W / 2, yy + i * lh, { ...o, align: 'center', color: '#f4f7ff' }));
    c.restore();
  }
}

// ------------------------------------------------------------------ scene context
function ctxFor(sc, t) {
  const L = sc.lines;
  return {
    t, dur: sc.dur, ch: sc.ch, acc: ACC[sc.ch], sc, L,
    at: i => (L[i] ? L[i].s : 1e9), end: i => (L[i] ? L[i].e : 1e9),
    pz: i => sc.pauses[i] || { s: 1e9, e: 1e9 },
    // lip-sync amplitude for a speaker at local time
    amp(who) {
      for (const l of L) if (l.who === who && t >= l.s && t < l.e) { const v = l.env[Math.floor((t - l.s) * TL.fps)] || 0; return clamp(v * 1.2); }
      return 0;
    },
    talking(who) { return L.some(l => l.who === who && t >= l.s - .2 && t < l.e + .2); },
    // which line index is current/last started
    cur() { let k = -1; L.forEach((l, i) => { if (t >= l.s) k = i; }); return k; },
  };
}

// ------------------------------------------------------------------ transitions + frame
const BUF = [document.createElement('canvas'), document.createElement('canvas')];
BUF.forEach(b => { b.width = W; b.height = H; });
const TRANS = ['zoom', 'sweep', 'iris', 'slice', 'push', 'flash', 'blur', 'zoom', 'iris', 'sweep', 'push', 'slice'];
const TW = 0.45; // half-window seconds
function drawScene(c, sc, t, gt) {
  c.save();
  background(c, sc.ch, gt, 0);
  const fn = SCENES[sc.type];
  // subtle global camera breathing (dolly)
  const k = 1 + 0.018 * Math.sin(gt * .21) ;
  c.translate(W / 2, H / 2); c.scale(k, k); c.translate(-W / 2, -H / 2);
  if (fn) fn(c, ctxFor(sc, t)); else txt(c, sc.type, 100, 100);
  c.restore();
}
function composite(c, A, B, p, kind, accB) {
  const e = E.io(p);
  c.save();
  switch (kind) {
    case 'zoom':
      c.globalAlpha = 1; c.save(); c.translate(W / 2, H / 2); c.scale(1 + e * .5, 1 + e * .5); c.translate(-W / 2, -H / 2); c.globalAlpha = 1 - e; c.drawImage(A, 0, 0); c.restore();
      c.save(); c.translate(W / 2, H / 2); c.scale(.82 + .18 * e, .82 + .18 * e); c.translate(-W / 2, -H / 2); c.globalAlpha = e; c.drawImage(B, 0, 0); c.restore(); break;
    case 'iris': {
      c.drawImage(A, 0, 0); c.save(); c.beginPath(); const r = e * W * .62; c.arc(W / 2, H / 2, r, 0, 7); c.clip(); c.drawImage(B, 0, 0); c.restore();
      c.strokeStyle = hexA(accB, (1 - e) * .9); c.lineWidth = 3; c.beginPath(); c.arc(W / 2, H / 2, e * W * .62, 0, 7); c.stroke(); break;
    }
    case 'slice': {
      c.drawImage(A, 0, 0); const n = 9, sh = H / n;
      for (let i = 0; i < n; i++) { const q = E.out(clamp(p * 1.6 - i * .07)); const dx = (i % 2 ? 1 : -1) * (1 - q) * W; c.drawImage(B, 0, i * sh, W, sh + 1, dx, i * sh, W, sh + 1); }
      break;
    }
    case 'sweep': {
      const x = lerp(-200, W + 200, e);
      c.drawImage(A, 0, 0); c.save(); c.beginPath(); c.moveTo(0, 0); c.lineTo(x + 120, 0); c.lineTo(x - 120, H); c.lineTo(0, H); c.clip(); c.drawImage(B, 0, 0); c.restore();
      c.save(); c.globalCompositeOperation = 'lighter'; const g = c.createLinearGradient(x - 160, 0, x + 160, 0); g.addColorStop(0, hexA(accB, 0)); g.addColorStop(.5, hexA(accB, .55)); g.addColorStop(1, hexA(accB, 0));
      c.fillStyle = g; c.beginPath(); c.moveTo(x + 40, 0); c.lineTo(x + 200, 0); c.lineTo(x - 40, H); c.lineTo(x - 200, H); c.fill(); c.restore(); break;
    }
    case 'push':
      c.drawImage(A, -e * W * .35, 0); c.globalAlpha = 1; c.save(); c.globalAlpha = 1 - e * .0; c.drawImage(B, (1 - e) * W, 0); c.restore();
      c.fillStyle = `rgba(0,0,0,${.5 * Math.sin(e * Math.PI)})`; c.fillRect(0, 0, (1 - e) * W, H); break;
    case 'flash':
      c.drawImage(e < .5 ? A : B, 0, 0); c.save(); c.globalCompositeOperation = 'lighter'; c.fillStyle = hexA(accB, .7 * Math.sin(e * Math.PI)); c.fillRect(0, 0, W, H); c.restore(); break;
    case 'blur':
      c.filter = `blur(${Math.sin(e * Math.PI) * 18}px)`; c.globalAlpha = 1; c.drawImage(A, 0, 0); c.globalAlpha = e; c.drawImage(B, 0, 0); c.filter = 'none'; break;
  }
  c.restore();
}
function sceneAt(gt) {
  const S = TL.scenes; let i = S.findIndex(s => gt < s.start + s.dur); if (i < 0) i = S.length - 1; return i;
}
function renderAt(gt) {
  const frame = Math.round(gt * TL.fps);
  const S = TL.scenes; const i = sceneAt(gt); const sc = S[i];
  const t = gt - sc.start;
  let other = null, p = 0, kind;
  if (t < TW && i > 0) { other = S[i - 1]; p = .5 + t / (2 * TW); kind = TRANS[(i - 1) % TRANS.length]; }
  else if (sc.dur - t < TW && i < S.length - 1) { other = S[i + 1]; p = .5 - (sc.dur - t) / (2 * TW); kind = TRANS[i % TRANS.length]; }
  if (other) {
    const [A, B] = t < TW ? [other, sc] : [sc, other];
    const a = BUF[0].getContext('2d'), b = BUF[1].getContext('2d');
    drawScene(a, A, gt - A.start, gt); drawScene(b, B, Math.max(0, gt - B.start), gt);
    composite(ctx, BUF[0], BUF[1], p, kind, ACC[B.ch]);
  } else drawScene(ctx, sc, t, gt);
  hud(ctx, sc, t, gt);
  subtitles(ctx, sc, t);
  // global fade in/out
  const fi = 1 - P(gt, 0, 1.2), fo = P(gt, TL.duration - 2.0, TL.duration - .2);
  if (fi + fo > 0) { ctx.fillStyle = `rgba(0,0,0,${Math.max(fi, fo)})`; ctx.fillRect(0, 0, W, H); }
  post(ctx, frame);
}
const SCENES = {};
