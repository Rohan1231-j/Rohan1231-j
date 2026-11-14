// NEURAL HORIZON — scene renderers. Each gets (c, S) where S = ctxFor(scene, localTime).
// Visual beats are keyed to narration line start times (S.at(i)) so picture follows voice.
'use strict';

// ============================================================== PROLOGUE
const SPHERE = Array.from({ length: 1300 }, (_, i) => {
  const n = 1300, k = i + .5, phi = Math.acos(1 - 2 * k / n), th = Math.PI * (1 + Math.sqrt(5)) * k;
  const r0 = 900 + hash(i) * 1400, a0 = hash(i + 1) * 6.28, b0 = hash(i + 2) * 3.14;
  return { sx: Math.cos(th) * Math.sin(phi), sy: Math.cos(phi), sz: Math.sin(th) * Math.sin(phi),
    cx: Math.cos(a0) * Math.sin(b0) * r0, cy: Math.cos(b0) * r0 * .6, cz: Math.sin(a0) * Math.sin(b0) * r0, h: hash(i + 9) };
});
SCENES.cold_open = (c, S) => {
  const t = S.t;
  const conv = E.io(P(t, .2, S.at(1) - .3));
  const dive = E.in(P(t, S.at(2) - .2, S.at(2) + 2.6));
  const cam = { yaw: t * .22, pitch: .25 + Math.sin(t * .2) * .1, dist: lerp(1250, 420, dive), f: 1000 };
  const R = 300 * (1 + .03 * Math.sin(t * 2));
  c.save(); c.globalCompositeOperation = 'lighter';
  for (const p of SPHERE) {
    const wob = 1 + .05 * Math.sin(t * 1.5 + p.h * 20);
    const x = lerp(p.cx, p.sx * R * wob, conv), y = lerp(p.cy, p.sy * R * wob, conv), z = lerp(p.cz, p.sz * R * wob, conv);
    const [sx, sy, f, Z] = proj(x, y, z, cam); if (Z < 30) continue;
    const col = p.h > .7 ? '#a68bff' : p.h > .4 ? '#4de8ff' : '#e8f6ff';
    const a = clamp(f * .9) * (1 - dive * .7);
    c.fillStyle = hexA(col, a * .85); const r = 1.1 + f * 1.8; c.fillRect(sx - r / 2, sy - r / 2, r, r);
  }
  // core glow
  glowDot(c, W / 2, H / 2, 380 * (1 + dive * 2), '#4de8ff', .22 * conv);
  c.restore();
  // kinetic words for line 0
  const w0 = ['WRITES', 'REASONS', 'BUILDS'];
  const L0 = S.at(0);
  w0.forEach((w, i) => {
    const tw = L0 + 2.4 + i * .75; const a = P(t, tw, tw + .5) * (1 - P(t, S.at(1) - .4, S.at(1)));
    kinetic(c, w, W / 2 + (i - 1) * 380, 300, P(t, tw, tw + .7), { size: 54, w: 700, f: F.head, ls: 12, align: 'center', a, color: i === 1 ? '#a68bff' : '#e8f6ff' });
  });
  // line 1: orbiting capability labels (motion-tracked)
  const caps = ['translate', 'summarize', 'write code', 'plan', 'explain', 'analyze'];
  const la = P(t, S.at(1), S.at(1) + 1) * (1 - P(t, S.at(2), S.at(2) + .8));
  if (la > 0) caps.forEach((s, i) => {
    const ang = i / caps.length * 6.283 + t * .3;
    const [ax, ay] = proj(Math.cos(ang) * R, Math.sin(i * 2) * 120, Math.sin(ang) * R, cam);
    const [lx, ly] = proj(Math.cos(ang) * 520, Math.sin(i * 2) * 200, Math.sin(ang) * 520, cam);
    tag(c, ax, ay, lx, ly, s.toUpperCase(), i % 2 ? '#a68bff' : '#4de8ff', la * P(t, S.at(1) + i * .2, S.at(1) + i * .2 + .8));
  });
  // "?" at the core on line 1
  txt(c, '?', W / 2, H / 2 + 50, { size: 150, w: 700, f: F.head, align: 'center', color: '#ffffff', a: la * .9 * (0.8 + .2 * Math.sin(t * 3)) });
  // line 2: Nova silhouette rises out of the light
  const na = P(t, S.at(2) + .4, S.at(2) + 2.2);
  if (na > 0) {
    glowDot(c, W / 2, 940, 520, '#4de8ff', .35 * na);
    person(c, 'NOVA', W / 2, 1010 + (1 - E.out(na)) * 120, 1.25, { t, silhouette: true, a: na });
    txt(c, 'ONE BEGINNER.', W / 2, 330, { size: 30, w: 600, f: F.mono, ls: 14, align: 'center', a: P(t, S.at(2) + 1.6, S.at(2) + 2.4), color: '#bfefff' });
  }
};

SCENES.title = (c, S) => {
  const t = S.t;
  // perspective horizon grid
  const hy = 640;
  c.save();
  const sun = c.createRadialGradient(W / 2, hy, 10, W / 2, hy, 900); sun.addColorStop(0, 'rgba(120,220,255,0.35)'); sun.addColorStop(.3, 'rgba(110,90,255,0.12)'); sun.addColorStop(1, 'rgba(0,0,0,0)');
  c.fillStyle = sun; c.fillRect(0, 0, W, H);
  c.strokeStyle = 'rgba(120,200,255,0.22)'; c.lineWidth = 1.2;
  for (let i = -24; i <= 24; i++) { c.beginPath(); c.moveTo(W / 2 + i * 14, hy); c.lineTo(W / 2 + i * 260, H + 200); c.stroke(); }
  for (let k = 0; k < 18; k++) { const z = ((k + (t * .9) % 1) / 18); const y = hy + Math.pow(z, 2.4) * (H - hy + 300); c.globalAlpha = z; c.beginPath(); c.moveTo(0, y); c.lineTo(W, y); c.stroke(); }
  c.globalAlpha = 1; glowLine(c, [[0, hy], [W, hy]], '#7fe7ff', .6, 1.5);
  c.restore();
  const p = E.out(P(t, .3, 2.6));
  const o = { size: 150, w: 700, f: F.head, ls: lerp(70, 22, p), align: 'center' };
  // title with light sweep
  kinetic(c, 'NEURAL HORIZON', W / 2, 470, P(t, .2, 2.2), { ...o, color: '#f2f7ff', rise: 60 });
  const sx = lerp(-400, W + 400, P(t, 1.6, 3.4));
  if (sx > -300 && sx < W + 300) {
    const g = c.createLinearGradient(sx - 200, 0, sx + 200, 0); g.addColorStop(0, 'rgba(77,232,255,0)'); g.addColorStop(.5, 'rgba(160,240,255,1)'); g.addColorStop(1, 'rgba(77,232,255,0)');
    txt(c, 'NEURAL HORIZON', W / 2, 470, { ...o, color: g });
  }
  txt(c, 'A JOURNEY INTO ARTIFICIAL INTELLIGENCE', W / 2, 545, { size: 26, w: 600, f: F.mono, ls: 12, align: 'center', color: '#9fe9ff', a: P(t, 1.8, 2.8) });
  txt(c, 'An animated documentary in eight chapters', W / 2, 605, { size: 24, w: 500, align: 'center', color: '#c3cde6', a: P(t, 2.8, 3.8) * (1 - P(t, 5.6, 6.3)) });
  // lens flare streak
  glowLine(c, [[W / 2 - 600 * p, 470 - 60], [W / 2 + 600 * p, 470 - 60]], '#4de8ff', .25 * (1 - P(t, 3, 5)), 1);
};

// ============================================================== CHAPTER INTROS
const MOTIF = {
  1: (c, t, a) => { c.save(); c.globalCompositeOperation = 'lighter'; for (let i = 0; i < 500; i++) { const r = 40 + hash(i) * 520, ang = hash(i + 4) * 6.28 + t * (.4 - r / 2000) + r * .006; c.fillStyle = hexA(i % 3 ? '#4de8ff' : '#a68bff', a * .55); c.fillRect(1300 + Math.cos(ang) * r * 1.3, 540 + Math.sin(ang) * r * .55, 2.2, 2.2); } c.restore(); },
  2: (c, t, a) => { for (let k = 0; k < 7; k++) { const cam = { yaw: -.6 + Math.sin(t * .3) * .1, pitch: .5, dist: 1500, cx: 1350, cy: 560 }; const z = (k - 3) * 110; const pts = [[-260, 0, -260], [260, 0, -260], [260, 0, 260], [-260, 0, 260]].map(q => proj(q[0], q[1] + z, q[2], cam)); c.beginPath(); pts.forEach((q, i) => i ? c.lineTo(q[0], q[1]) : c.moveTo(q[0], q[1])); c.closePath(); c.fillStyle = hexA('#a68bff', a * .06); c.fill(); c.strokeStyle = hexA('#a68bff', a * .55); c.lineWidth = 1.5; c.stroke(); } },
  3: (c, t, a) => { for (let i = 0; i < 26; i++) { const x = 900 + i * 40, sp = 80 + hash(i) * 120; for (let k = 0; k < 6; k++) { const y = ((t * sp + k * 210 + hash(i + k) * 300) % 1300) - 150; c.globalAlpha = a * .5 * (1 - Math.abs(y - 540) / 700); rr(c, x, y, 34, 22, 6); c.strokeStyle = '#ffb547'; c.lineWidth = 1.2; c.stroke(); txt(c, String((i * 37 + k * 11) % 99), x + 17, y + 16, { size: 11, f: F.mono, align: 'center', color: '#ffb547' }); } } c.globalAlpha = 1; },
  4: (c, t, a) => { const cam = { yaw: t * .25, pitch: .35, dist: 1300, cx: 1330, cy: 540 }; c.save(); c.globalCompositeOperation = 'lighter'; for (let i = 0; i < 360; i++) { const [x, y, f] = proj((hash(i) - .5) * 700, (hash(i + 1) - .5) * 500, (hash(i + 2) - .5) * 700, cam); c.fillStyle = hexA('#3df5b0', a * .7 * f); c.beginPath(); c.arc(x, y, 2.2 * f, 0, 7); c.fill(); } c.restore(); },
  5: (c, t, a) => { const o = { cx: 1300, cy: 420, k: 1 }; for (let i = -6; i <= 6; i++) for (let j = -6; j <= 6; j++) { const d = Math.hypot(i, j); const pulse = Math.max(0, Math.sin(d * .9 - t * 3)); const [x, y] = iso(i * 70, j * 70, 0, o); c.fillStyle = hexA('#ff5fa2', a * (.12 + pulse * .5) * (1 - d / 9)); c.beginPath(); c.arc(x, y, 3 + pulse * 3, 0, 7); c.fill(); } },
  6: (c, t, a) => { const o = { cx: 1320, cy: 600, k: 1 }; for (let i = 0; i < 5; i++) for (let j = 0; j < 5; j++) { const h = 30 + (hash(i * 5 + j) * 160) * E.out(clamp(t * .6 - (i + j) * .08)); isoBox(c, (i - 2.5) * 80, (j - 2.5) * 80, 0, 64, 64, h, o, ['rgba(255,170,130,0.55)', 'rgba(140,60,40,0.55)', 'rgba(90,35,25,0.55)'], a * .8); } },
  7: (c, t, a) => { c.save(); c.translate(1350, 540); c.globalAlpha = a; c.beginPath(); c.moveTo(0, -250); c.quadraticCurveTo(200, -210, 210, -150); c.quadraticCurveTo(200, 120, 0, 260); c.quadraticCurveTo(-200, 120, -210, -150); c.quadraticCurveTo(-200, -210, 0, -250); c.strokeStyle = '#7ab8ff'; c.lineWidth = 3; c.stroke(); c.clip(); for (let y = -260; y < 270; y += 14) { c.fillStyle = hexA('#7ab8ff', .08 + .3 * Math.max(0, Math.sin(y * .03 - t * 4))); c.fillRect(-220, y, 440, 3); } c.restore(); },
  8: (c, t, a) => { const cx = 1340, cy = 760; for (let i = 0; i < 24; i++) { const ang = Math.PI + i / 23 * Math.PI; glowLine(c, [[cx + Math.cos(ang) * 120, cy + Math.sin(ang) * 120], [cx + Math.cos(ang) * (420 + 60 * Math.sin(t + i)), cy + Math.sin(ang) * (420 + 60 * Math.sin(t + i))]], '#ffd27a', a * .35, 1.2); } c.save(); c.beginPath(); c.rect(cx - 700, cy - 700, 1400, 700); c.clip(); glowDot(c, cx, cy, 300, '#ffd27a', a * .5); c.restore(); glowLine(c, [[cx - 600, cy], [cx + 600, cy]], '#ffd27a', a, 2); },
};
SCENES.chapter = (c, S) => {
  const t = S.t, ch = S.ch, acc = S.acc;
  MOTIF[ch](c, t, P(t, 0, 1));
  const num = String(ch).padStart(2, '0');
  // giant outline number with parallax
  txt(c, num, 170 + t * 12, 640, { size: 420, w: 700, f: F.head, stroke: hexA(acc, .35), lw: 2, a: P(t, 0, .8) });
  txt(c, `CHAPTER ${num}`, 200, 380, { size: 22, w: 600, f: F.mono, ls: 10, color: acc, a: P(t, .2, .8) });
  const title = TL.chapters[ch][0].toUpperCase(); const p = P(t, .35, 1.8);
  const o = { size: 96, w: 700, f: F.head, ls: 4, color: '#f4f7ff' };
  const style = ch % 3;
  if (style === 0) kinetic(c, title, 196, 500, p, o);
  else if (style === 1) { c.save(); c.beginPath(); c.rect(190, 400, 40 + 1500 * E.io(p), 140); c.clip(); txt(c, title, 196, 500, o); c.restore(); glowLine(c, [[196 + 1500 * E.io(p) * .9, 410], [196 + 1500 * E.io(p) * .9, 520]], acc, (1 - P(t, 1.6, 2)) * P(t, .35, .5), 2); }
  else txt(c, scramble(title, p, ch), 196, 500, o);
  txt(c, TL.chapters[ch][1], 200, 570, { size: 30, w: 400, color: '#c9d3ea', a: P(t, 1.2, 2) });
  // stage chip
  const st = TL.ch_stage[ch]; const prevSt = TL.ch_stage[ch - 1] ?? 0;
  const up = st > prevSt && ch > 1;
  const pw = pill(c, `NOVA · ${TL.stages[st].toUpperCase()}`, 200, 650, STAGE_COL[st], { a: P(t, 1.6, 2.2), size: 18 });
  if (up) pill(c, '▲ LEVEL UP', 200 + pw + 14, 650, STAGE_COL[st], { a: P(t, 2.0, 2.4) * (0.75 + .25 * Math.sin(t * 8)), size: 18, solid: true });
  // chapter progress dots
  for (let i = 1; i <= 8; i++) {
    const x = 200 + (i - 1) * 46; const on = i <= ch;
    c.fillStyle = i === ch ? acc : on ? hexA(ACC[i], .7) : 'rgba(255,255,255,0.15)';
    c.beginPath(); c.arc(x, 760, i === ch ? 7 : 5, 0, 7); c.fill(); if (i === ch) glowDot(c, x, 760, 30, acc, .8);
  }
};

// ============================================================== CH1 — THE SPARK
SCENES.nova_meets = (c, S) => {
  const t = S.t;
  const zoomOut = E.io(P(t, S.at(4), S.at(4) + 2.2));
  // Nova
  const nx = lerp(470, 300, zoomOut);
  glowDot(c, nx, 960, 420, '#4de8ff', .12);
  person(c, 'NOVA', nx, 960, 1.35 * (1 - zoomOut * .25), { t, amp: S.amp('NOVA'), look: .6, stage: 0 });
  tag(c, nx + 40, 960 - 600 * (1 - zoomOut * .25), nx + 220, 250, 'NOVA · BEGINNER', '#4de8ff', P(t, S.at(1), S.at(1) + .8));
  ['CURIOUS', 'A LITTLE SKEPTICAL', 'STARTING FROM ZERO'].forEach((s, i) => {
    const ti = S.at(1) + 1.3 + i * .8; pill(c, s, nx + 200, 330 + i * 52, '#7fe7ff', { a: P(t, ti, ti + .4) * (1 - P(t, S.at(2), S.at(2) + .6)), size: 16 });
  });
  // holo panel
  const px = lerp(900, 760, zoomOut), py = lerp(190, 300, zoomOut), pw = lerp(880, 400, zoomOut), ph = lerp(590, 270, zoomOut);
  const pa = P(t, .2, 1);
  // background galaxy of text (line 4)
  if (zoomOut > 0) {
    const frag = ['the cat sat on', 'water boils at 100°C', 'therefore x = 4', 'once upon a time', 'def sort(items):', 'Paris is the capital', 'if it rains, then', 'photosynthesis converts', 'bonjour, comment', 'the derivative of'];
    c.save();
    for (let i = 0; i < 90; i++) {
      const ang = hash(i) * 6.28 + t * .05 * (hash(i + 1) > .5 ? 1 : -1), r = 300 + hash(i + 2) * 700;
      const x = 1180 + Math.cos(ang) * r * 1.2, y = 520 + Math.sin(ang) * r * .5;
      txt(c, frag[i % frag.length], x, y, { size: 12 + hash(i + 3) * 10, f: F.mono, color: hash(i) > .5 ? '#7fe7ff' : '#a68bff', a: zoomOut * (.08 + hash(i + 5) * .2) * (y < 170 ? 0 : 1), align: 'center' });
    }
    c.restore();
    const words = [['GRAMMAR', S.at(4) + 2.1], ['FACTS', S.at(4) + 2.9], ['PATTERNS OF REASONING', S.at(4) + 3.6]];
    words.forEach(([w, tw], i) => kinetic(c, w, 1180, 640 + i * 70, P(t, tw, tw + .7), { size: 44, w: 700, f: F.head, ls: 6, align: 'center', color: i === 2 ? '#4de8ff' : '#f4f7ff' }));
    txt(c, 'TRAINED ON TRILLIONS OF TOKENS OF TEXT', 1180, 250, { size: 18, w: 600, f: F.mono, ls: 6, align: 'center', color: '#7fe7ff', a: P(t, S.at(4) + 1.2, S.at(4) + 2) });
  }
  glass(c, px, py, pw, ph, { acc: '#4de8ff', a: pa });
  c.save(); c.beginPath(); rr(c, px, py, pw, ph, 22); c.clip();
  c.translate(px, py); const k = pw / 880; c.scale(k, k);
  // phase A: buzzwords + question marks
  const aA = 1 - P(t, S.at(2) - .3, S.at(2) + .3);
  if (aA > 0) {
    [['AI', 90, 120], ['LLM', 620, 110], ['GPT?', 120, 470], ['AGENTS', 600, 500], ['TOKENS', 80, 300], ['RAG?', 680, 300], ['PROMPTS', 330, 560]].forEach(([w, x0, y0], i) => {
      const x = x0 + Math.sin(t + i) * 14, y = y0 + Math.cos(t * .8 + i) * 10;
      txt(c, w, x, y, { size: 30 + (i % 3) * 10, w: 700, f: F.head, color: i % 2 ? '#a68bff' : '#7fe7ff', a: aA * .7 });
    });
    txt(c, '?', 440, 380, { size: 220, w: 700, f: F.head, align: 'center', color: '#fff', a: aA * (.5 + .2 * Math.sin(t * 3)) });
  }
  // phase B: LLM concept (line 2)
  const aB = P(t, S.at(2), S.at(2) + .6) * (1 - P(t, S.at(3) - .4, S.at(3) + .2));
  if (aB > 0) {
    txt(c, 'LARGE LANGUAGE MODEL', 440, 80, { size: 22, w: 700, f: F.mono, ls: 8, align: 'center', color: '#7fe7ff', a: aB });
    const q = P(t, S.at(2) + 1, S.at(2) + 7);
    // corpus stack
    for (let i = 0; i < 14; i++) { c.globalAlpha = aB * P(q, i / 30, i / 30 + .2); rr(c, 70 + (i % 2) * 8, 150 + i * 22, 190 - (i * 37) % 60, 10, 5); c.fillStyle = '#a68bff'; c.fill(); }
    c.globalAlpha = 1;
    txt(c, 'Enormous text', 165, 500, { size: 22, align: 'center', color: DIM, a: aB });
    flow(c, 290, 300, 380, 300, t, P(q, .25, .45), '#7fe7ff', { a: aB });
    // network
    const nodes = []; [3, 5, 5, 3].forEach((n, li) => { for (let j = 0; j < n; j++) nodes.push([430 + li * 70, 300 + (j - (n - 1) / 2) * 52, li]); });
    for (const a of nodes) for (const b of nodes) if (b[2] === a[2] + 1) { c.strokeStyle = hexA('#4de8ff', .25 * aB * P(q, .4, .6)); c.lineWidth = 1; c.beginPath(); c.moveTo(a[0], a[1]); c.lineTo(b[0], b[1]); c.stroke(); }
    nodes.forEach((n, i) => { glowDot(c, n[0], n[1], 18, '#4de8ff', aB * P(q, .4, .6) * (.5 + .5 * Math.sin(t * 4 + i))); c.fillStyle = hexA('#e8f6ff', aB * P(q, .4, .6)); c.beginPath(); c.arc(n[0], n[1], 5, 0, 7); c.fill(); });
    txt(c, 'Model', 535, 500, { size: 22, align: 'center', color: DIM, a: aB });
    flow(c, 660, 300, 720, 300, t, P(q, .65, .8), '#7fe7ff', { a: aB });
    txt(c, 'next', 790, 290, { size: 30, w: 700, f: F.head, align: 'center', color: '#fff', a: aB * P(q, .8, .9) });
    txt(c, 'word?', 790, 326, { size: 30, w: 700, f: F.head, align: 'center', color: '#fff', a: aB * P(q, .8, .9) });
  }
  // phase C: next-word prediction demo (line 3)
  const aC = P(t, S.at(3) - .2, S.at(3) + .4);
  if (aC > 0) {
    txt(c, 'PREDICT THE NEXT TOKEN', 440, 80, { size: 22, w: 700, f: F.mono, ls: 8, align: 'center', color: '#7fe7ff', a: aC });
    const fill = P(t, S.at(3) + 2.2, S.at(3) + 2.8);
    txt(c, 'The cat sat on the', 90, 190, { size: 44, w: 600, f: F.head, a: aC });
    const bx = 90 + measure(c, 'The cat sat on the ', { size: 44, w: 600, f: F.head });
    c.globalAlpha = aC; c.setLineDash([8, 8]); c.strokeStyle = '#7fe7ff'; c.lineWidth = 2; c.beginPath(); c.moveTo(bx, 200); c.lineTo(bx + 110, 200); c.stroke(); c.setLineDash([]); c.globalAlpha = 1;
    txt(c, 'mat', bx + 4, 190 - (1 - E.back(fill)) * 200, { size: 44, w: 700, f: F.head, color: '#4de8ff', a: fill });
    const cands = [['mat', .62], ['floor', .18], ['sofa', .09], ['roof', .04], ['…', .07]];
    cands.forEach(([w, p], i) => {
      const y = 270 + i * 54, q = E.out(P(t, S.at(3) + .1 + i * .1, S.at(3) + 1.2 + i * .1));
      txt(c, w, 90, y + 8, { size: 26, w: 600, f: F.mono, a: aC, color: i === 0 ? '#4de8ff' : '#cfd8ee' });
      bar(c, 220, y - 10, 480, 18, p * q / .62 * .95, i === 0 ? '#4de8ff' : '#a68bff');
      txt(c, Math.round(p * 100 * q) + '%', 760, y + 8, { size: 24, w: 600, f: F.mono, a: aC, color: '#cfd8ee' });
    });
    txt(c, 'illustrative probabilities', 90, 560, { size: 16, f: F.mono, color: DIM, a: aC });
  }
  c.restore();
};

// ============================================================== CH2 — INSIDE THE MACHINE
const TOK = [['Why', 10445], [' is', 382], [' the', 290], [' sky', 17307], [' blue', 9861], ['?', 30]];
const TOKCOL = ['#4de8ff', '#a68bff', '#ff5fa2', '#3df5b0', '#7ab8ff', '#ffb547'];
SCENES.llm_journey = (c, S) => {
  const t = S.t;
  const stops = [0, 1920, 3840, 5760, 7680];
  let camX = 0; for (let i = 1; i < 5; i++) camX += (stops[i] - stops[i - 1]) * E.io(P(t, S.at(i) - .3, S.at(i) + 1.1));
  // parallax backdrop grid
  c.save(); c.strokeStyle = 'rgba(166,139,255,0.07)'; c.lineWidth = 1;
  for (let x = -((camX * .4) % 120); x < W; x += 120) { c.beginPath(); c.moveTo(x, 160); c.lineTo(x, 900); c.stroke(); }
  c.restore();
  // pipeline indicator
  const steps = ['INPUT', 'TOKENS', 'EMBEDDINGS', 'TRANSFORMER LAYERS', 'NEXT TOKEN'];
  const curStep = S.cur();
  let sx = W / 2 - 560;
  steps.forEach((s, i) => {
    const on = i <= curStep, now = i === curStep;
    const w = pill(c, `${i + 1}  ${s}`, sx, 190, now ? '#a68bff' : on ? '#6f5bbf' : '#3a4060', { size: 15, solid: now, a: P(t, .3, 1), tc: on ? TXT : DIM });
    if (i < 4) { c.fillStyle = on ? '#a68bff' : '#3a4060'; c.fillRect(sx + w + 4, 189, 14, 2); }
    sx += w + 22;
  });
  c.save(); c.translate(-camX, 0);
  // ---- stop 0: input
  { const x0 = 0;
    person(c, 'NOVA', x0 + 360, 900, .95, { t, stage: 1, look: .7 });
    glass(c, x0 + 640, 400, 760, 150, { acc: '#a68bff' });
    const q = typed('Why is the sky blue?', P(t, .6, 2.6));
    txt(c, q + ((t * 2) % 1 < .5 && t < 3.4 ? '|' : ''), x0 + 690, 495, { size: 56, w: 600, f: F.head });
    txt(c, 'PROMPT', x0 + 670, 380, { size: 16, w: 700, f: F.mono, ls: 5, color: '#a68bff' });
    flow(c, x0 + 1420, 475, x0 + 1800, 475, t, P(t, 2.8, 3.6), '#a68bff');
  }
  // ---- stop 1: tokens
  { const x0 = 1920; const p = P(t, S.at(1) + .6, S.at(1) + 2.6);
    let x = x0 + 330; const y = 470;
    TOK.forEach(([s, id], i) => {
      const q = E.back(clamp(p * 1.6 - i * .12)); const w = measure(c, s.replace(' ', '␣'), { size: 46, w: 600, f: F.mono }) + 40;
      const xx = lerp(x0 + 760, x, q);
      glass(c, xx, y - 60, w, 90, { acc: TOKCOL[i], a: clamp(q), r: 14 });
      txt(c, s.replace(' ', '␣'), xx + 20, y + 2, { size: 46, w: 600, f: F.mono, color: TOKCOL[i], a: clamp(q) });
      const idp = P(t, S.at(1) + 4.2 + i * .15, S.at(1) + 5 + i * .15);
      txt(c, fmt(id * E.out(idp)), xx + w / 2, y + 90, { size: 28, w: 600, f: F.mono, align: 'center', a: idp, color: '#e8eaff' });
      x += w + 28;
    });
    txt(c, 'TOKEN IDs (ILLUSTRATIVE) · ␣ = LEADING SPACE', x0 + 330, y + 150, { size: 16, f: F.mono, ls: 3, color: DIM, a: P(t, S.at(1) + 5, S.at(1) + 6) });
    // word pieces
    const wp = P(t, S.at(1) + 2.6, S.at(1) + 3.6);
    txt(c, 'unbelievable  →', x0 + 330, 760, { size: 32, w: 500, f: F.mono, a: wp, color: '#cfd8ee' });
    ['un', 'believ', 'able'].forEach((s, i) => pill(c, s, x0 + 680 + i * 150, 750, TOKCOL[i + 1], { size: 24, f: F.mono, a: P(wp * 3 - i, 0, 1) }));
    txt(c, 'pieces of words', x0 + 1160, 760, { size: 22, color: DIM, a: wp });
  }
  // ---- stop 2: embeddings
  { const x0 = 3840; const p = P(t, S.at(2) + .4, S.at(2) + 3);
    TOK.forEach(([s], i) => {
      const x = x0 + 260 + i * 120;
      txt(c, s.trim() || s, x, 300, { size: 24, w: 600, f: F.mono, align: 'center', color: TOKCOL[i], a: P(t, S.at(2), S.at(2) + .5) });
      for (let k = 0; k < 10; k++) {
        const v = Math.sin(i * 3.1 + k * 1.7) * Math.cos(k * .7 + i);
        const q = clamp(p * 2 - k * .08 - i * .05);
        rr(c, x - 40, 330 + k * 46, 80, 38, 8);
        c.fillStyle = v > 0 ? hexA('#4de8ff', .15 + Math.abs(v) * .7 * q) : hexA('#ff5fa2', .15 + Math.abs(v) * .7 * q); c.fill();
        if (i === 3) txt(c, (v >= 0 ? ' ' : '−') + Math.abs(v).toFixed(2), x, 356 + k * 46, { size: 15, f: F.mono, align: 'center', a: q, color: '#fff' });
      }
    });
    txt(c, '⋮  thousands of values per token', x0 + 260 + 2.5 * 120, 850, { size: 20, f: F.mono, align: 'center', color: DIM, a: p });
    // meaning space
    const mp = P(t, S.at(2) + 3, S.at(2) + 4.5);
    glass(c, x0 + 1050, 280, 700, 560, { acc: '#a68bff', a: mp });
    txt(c, 'SPACE OF MEANING (2-D SKETCH)', x0 + 1080, 320, { size: 15, w: 700, f: F.mono, ls: 4, color: '#a68bff', a: mp });
    const pts = [['sky', 420, 380, 3], ['blue', 500, 440, 4], ['cloud', 360, 470, 3], ['ocean', 560, 530, 4], ['why', 160, 640, 0], ['how', 230, 700, 0], ['what', 120, 720, 0], ['cat', 560, 730, 1], ['dog', 620, 690, 1]];
    pts.forEach(([s, x, y, ci], i) => {
      const q = P(mp * 9 - i * .6, 0, 1); const X = x0 + 1050 + x, Y = y + Math.sin(t + i) * 4;
      glowDot(c, X, Y, 26, TOKCOL[ci], q); c.fillStyle = TOKCOL[ci]; c.globalAlpha = q; c.beginPath(); c.arc(X, Y, 6, 0, 7); c.fill(); c.globalAlpha = 1;
      txt(c, s, X + 12, Y - 10, { size: 20, f: F.mono, a: q });
    });
    txt(c, 'related meanings sit close together', x0 + 1080, 815, { size: 18, color: DIM, a: mp });
  }
  // ---- stop 3: transformer layers + attention
  { const x0 = 5760; const p = P(t, S.at(3) + .2, S.at(3) + 2);
    const cam = { yaw: -.55 + Math.sin(t * .25) * .06, pitch: .42, dist: 1650, cx: x0 + 620, cy: 560, f: 1000 };
    const NL = 8;
    for (let L = NL - 1; L >= 0; L--) {
      const y = (NL / 2 - L) * 70; const q = clamp(p * 1.6 - L * .07);
      const pts = [[-330, y, -170], [330, y, -170], [330, y, 170], [-330, y, 170]].map(v => proj(v[0], v[1], v[2], cam));
      c.beginPath(); pts.forEach((v, i) => i ? c.lineTo(v[0], v[1]) : c.moveTo(v[0], v[1])); c.closePath();
      c.fillStyle = hexA('#a68bff', .07 * q); c.fill(); c.strokeStyle = hexA('#a68bff', .6 * q); c.lineWidth = 1.4; c.stroke();
      for (let k = 0; k < 6; k++) {
        const [nx, ny] = proj(-250 + k * 100, y, 0, cam);
        const pulse = Math.max(0, Math.sin(t * 3 - L * .7 + k * .3));
        glowDot(c, nx, ny, 16, TOKCOL[k], q * (.3 + .6 * pulse));
      }
      if (L === 0 || L === NL - 1) { const [lx, ly] = proj(360, y, 170, cam); txt(c, L === 0 ? 'LAYER 1' : 'LAYER N', lx + 12, ly, { size: 16, w: 700, f: F.mono, ls: 3, color: '#a68bff', a: q }); }
    }
    txt(c, '× DOZENS OF LAYERS', x0 + 360, 850, { size: 20, w: 700, f: F.mono, ls: 5, color: '#a68bff', a: p });
    // attention panel
    const ap = P(t, S.at(3) + 4.2, S.at(3) + 5.4);
    glass(c, x0 + 1150, 260, 680, 560, { acc: '#a68bff', a: ap });
    txt(c, 'ATTENTION · "blue" looks at…', x0 + 1180, 305, { size: 18, w: 700, f: F.mono, ls: 2, color: '#a68bff', a: ap });
    const ws = [.12, .03, .05, .62, .1, .08];
    TOK.forEach(([s], i) => {
      const x = x0 + 1215 + i * 102, y = 700;
      txt(c, s.trim(), x + 30, y + 50, { size: 22, w: 600, f: F.mono, align: 'center', color: TOKCOL[i], a: ap });
      c.fillStyle = hexA(TOKCOL[i], ap); c.beginPath(); c.arc(x + 30, y + 10, 7, 0, 7); c.fill();
      if (i !== 4) {
        const q = E.out(P(t, S.at(3) + 5.2 + i * .12, S.at(3) + 6.4 + i * .12));
        const bx = x0 + 1215 + 4 * 102 + 30; const h = 60 + Math.abs(4 - i) * 50;
        c.save(); c.globalAlpha = ap * q; c.strokeStyle = '#a68bff'; c.lineWidth = 2 + ws[i] * 22; c.lineCap = 'round';
        c.beginPath(); c.moveTo(bx, y); c.bezierCurveTo(bx, y - h * 1.6, x + 30, y - h * 1.6, x + 30, y); c.stroke(); c.restore();
        txt(c, Math.round(ws[i] * 100) + '%', (bx + x + 30) / 2, y - h * 1.25, { size: 18, w: 600, f: F.mono, align: 'center', a: ap * q, color: i === 3 ? '#fff' : DIM });
      }
    });
    txt(c, 'illustrative weights', x0 + 1180, 800, { size: 15, f: F.mono, color: DIM, a: ap });
  }
  // ---- stop 4: next token + loop
  { const x0 = 7680; const p = P(t, S.at(4) + .3, S.at(4) + 2);
    glass(c, x0 + 160, 260, 760, 560, { acc: '#a68bff', a: p });
    txt(c, 'SCORES FOR THE NEXT TOKEN', x0 + 200, 310, { size: 17, w: 700, f: F.mono, ls: 4, color: '#a68bff', a: p });
    const C = [['Sunlight', .41], ['Because', .23], ['The', .15], ['Blue', .06], ['Light', .05]];
    C.forEach(([s, v], i) => {
      const y = 380 + i * 80; const q = E.out(P(t, S.at(4) + .8 + i * .12, S.at(4) + 2 + i * .12));
      txt(c, s, x0 + 200, y + 12, { size: 28, w: 600, f: F.mono, color: i === 0 ? '#fff' : '#b9c2dc', a: p });
      bar(c, x0 + 400, y - 8, 380, 22, v / .45 * q, i === 0 ? '#a68bff' : '#5d5aa0');
      txt(c, Math.round(v * 100 * q) + '%', x0 + 880, y + 12, { size: 22, f: F.mono, align: 'right', a: p, color: '#cfd8ee' });
    });
    const pick = P(t, S.at(4) + 3, S.at(4) + 3.4);
    if (pick > 0) { rr(c, x0 + 186, 350, 720, 64, 14); c.strokeStyle = hexA('#fff', pick); c.lineWidth = 2.5; c.stroke(); txt(c, 'PICKED', x0 + 880, 343, { size: 14, w: 700, f: F.mono, ls: 3, align: 'right', color: '#fff', a: pick }); }
    txt(c, 'illustrative scores', x0 + 200, 800, { size: 15, f: F.mono, color: DIM, a: p });
    // answer stream + loop
    glass(c, x0 + 1000, 330, 760, 250, { acc: '#4de8ff', a: P(t, S.at(4) + 3.4, S.at(4) + 4) });
    txt(c, 'ANSWER', x0 + 1030, 372, { size: 16, w: 700, f: F.mono, ls: 5, color: '#4de8ff', a: P(t, S.at(4) + 3.4, S.at(4) + 4) });
    const ans = 'Sunlight scatters off air molecules, and short blue wavelengths scatter far more than red.';
    const shown = typed(ans, P(t, S.at(4) + 4, S.at(4) + 10.5));
    para(c, shown + (shown.length < ans.length && shown.length ? '▍' : ''), x0 + 1030, 430, 700, { size: 32, w: 500, lh: 44 });
    // autoregressive loop arrow
    const lp = P(t, S.at(4) + 4.5, S.at(4) + 5.5);
    if (lp > 0) {
      c.save(); c.globalAlpha = lp; c.strokeStyle = '#4de8ff'; c.lineWidth = 2.5; c.setLineDash([10, 10]); c.lineDashOffset = -t * 40;
      c.beginPath(); c.moveTo(x0 + 1380, 590); c.bezierCurveTo(x0 + 1380, 720, x0 + 1100, 720, x0 + 935, 680); c.stroke(); c.restore();
      arrowHead(c, x0 + 935, 680, Math.PI * 1.08, '#4de8ff', lp);
      pill(c, '↻  ADD TOKEN TO THE TEXT · REPEAT', x0 + 1400, 735, '#4de8ff', { size: 18, align: 'center', a: lp });
    }
  }
  c.restore();
};

// ============================================================== QUIZ cards (ch2 + ch5)
function quizHeader(c, S, label, acc) {
  const t = S.t;
  pill(c, label, W / 2, 200, acc, { size: 20, align: 'center', solid: true, a: P(t, 0, .6) });
  const pz = S.pz(0);
  if (t > pz.s - .2 && t < pz.e + .6) {
    const a = P(t, pz.s - .2, pz.s + .2) * (1 - P(t, pz.e, pz.e + .6));
    const rem = Math.ceil(clamp(pz.e - t, 0, 9));
    ring(c, W / 2 + 330, 200, 30, P(t, pz.s, pz.e), acc, 5, a);
    txt(c, String(rem), W / 2 + 330, 210, { size: 26, w: 700, f: F.mono, align: 'center', a });
    txt(c, 'PAUSE & THINK', W / 2 - 330, 208, { size: 16, w: 700, f: F.mono, ls: 4, align: 'center', color: acc, a: a * (.6 + .4 * Math.sin(t * 6)) });
  }
}
SCENES.quiz = (c, S) => {
  const t = S.t, acc = S.acc;
  quizHeader(c, S, 'KNOWLEDGE CHECK', acc);
  const ga = P(t, .2, .9);
  glass(c, W / 2 - 600, 260, 1200, 560, { acc, a: ga });
  para(c, 'Does a language model look the answer up in a database before it replies?', W / 2 - 540, 340, 1080, { size: 40, w: 600, f: F.head, a: P(t, S.at(0) + .4, S.at(0) + 1.2) });
  const rev = P(t, S.at(1), S.at(1) + .6);
  const opts = [['A', 'Yes — it searches a database every time', false], ['B', 'No — it generates from patterns learned in training', true]];
  opts.forEach(([k, s, ok], i) => {
    const y = 480 + i * 120; const a = P(t, S.at(0) + 1.4 + i * .5, S.at(0) + 2 + i * .5);
    const col = rev ? (ok ? GOOD : BAD) : acc;
    c.save(); c.globalAlpha = a * (rev && !ok ? lerp(1, .45, rev) : 1);
    rr(c, W / 2 - 540, y, 1080, 92, 18); c.fillStyle = hexA(col, rev && ok ? .16 * rev : .06); c.fill(); c.strokeStyle = hexA(col, .7); c.lineWidth = 2; c.stroke();
    c.restore();
    txt(c, k, W / 2 - 490, y + 60, { size: 34, w: 700, f: F.head, color: col, a: a * (rev && !ok ? .5 : 1) });
    txt(c, s, W / 2 - 430, y + 58, { size: 30, w: 500, a: a * (rev && !ok ? .5 : 1) });
    if (rev) ok ? check(c, W / 2 + 480, y + 46, 50, GOOD, P(t, S.at(1) + .2, S.at(1) + .8)) : cross(c, W / 2 + 480, y + 46, 46, BAD, rev);
  });
  txt(c, 'Answers come from weights learned in training — unless the system adds retrieval (Chapter 04).', W / 2, 780, { size: 20, align: 'center', color: '#b9c6e4', a: P(t, S.at(1) + 3, S.at(1) + 4) });
};

// ============================================================== CH3 — THE COST OF WORDS
const BLK_A = [['System prompt', 900], ['Policy manual — all 40 pages', 14200], ['Full chat history', 3100], ['Task: summarize + draft reply', 200]];
const BLK_B = [['System prompt (concise)', 350], ['Relevant policy section only', 800], ['Conversation summary', 300], ['Task: summarize + draft reply', 200]];
SCENES.token_compare = (c, S) => {
  const t = S.t;
  // intro: Arjun + token fact
  const ia = 1 - P(t, S.at(1) - .2, S.at(1) + .5);
  if (ia > 0) {
    c.save(); c.globalAlpha = ia;
    person(c, 'ARJUN', 560, 960, 1.35, { t, amp: S.amp('ARJUN'), look: .5 });
    tag(c, 600, 380, 820, 300, 'ARJUN · AI ENGINEER', '#ffb547', P(t, .3, 1.1));
    glass(c, 1000, 300, 760, 420, { acc: '#ffb547' });
    txt(c, '1 TOKEN', 1060, 400, { size: 26, w: 700, f: F.mono, ls: 6, color: '#ffb547' });
    txt(c, '≈ ¾ of an English word', 1060, 470, { size: 46, w: 600, f: F.head });
    txt(c, 'rough rule of thumb', 1060, 510, { size: 20, color: DIM });
    // coin stream
    for (let i = 0; i < 12; i++) { const q = ((t * .6 + i / 12) % 1); const x = 1060 + q * 640, y = 620 + Math.sin(q * 6 + i) * 20; c.globalAlpha = ia * Math.sin(q * Math.PI); c.beginPath(); c.ellipse(x, y, 22, 22, 0, 0, 7); c.strokeStyle = '#ffb547'; c.lineWidth = 2; c.stroke(); txt(c, '$', x, y + 8, { size: 22, w: 700, align: 'center', color: '#ffb547' }); }
    c.restore();
  }
  const sa = P(t, S.at(1) - .1, S.at(1) + .8);
  if (sa <= 0) return;
  const slide = 1 - E.out(sa);
  const panels = [
    { x: 80 - slide * 900, title: 'WORKFLOW A', sub: 'Everything in the context window', col: '#ff8a5c', blocks: BLK_A, show: S.at(2) + .5, total: 18400, cost: '$55.20' },
    { x: 990 + slide * 900, title: 'WORKFLOW B', sub: 'Only the context that matters', col: GOOD, blocks: BLK_B, show: S.at(3) + .3, total: 1650, cost: '$4.95' },
  ];
  const feed = E.io(P(t, S.at(4) - .2, S.at(4) + 1.4));
  panels.forEach((pn, pi) => {
    const x = pn.x, y = 170, w = 850, h = 690;
    glass(c, x, y, w, h, { acc: pn.col });
    txt(c, pn.title, x + 36, y + 52, { size: 18, w: 700, f: F.mono, ls: 6, color: pn.col });
    txt(c, pn.sub, x + 36, y + 92, { size: 28, w: 600, f: F.head });
    // blocks stack
    let by = y + 585; let shownTok = 0;
    const blocks = [...pn.blocks].reverse(); // task first (bottom)
    blocks.forEach(([s, n], bi) => {
      const isTask = bi === 0;
      const tShow = isTask ? S.at(1) + .6 : pn.show + (bi - 1) * .9;
      const q = E.back(P(t, tShow, tShow + .7));
      const bh = Math.max(40, n * .017); by -= bh + 8;
      const yy = by + (1 - q) * -120 + feed * (y + 640 - by - bh / 2) * 0; // stay
      const fy = lerp(yy, y + 590, feed), fh = lerp(bh, 6, feed), fw = lerp(520, 80, feed);
      if (q <= 0) return;
      shownTok += n * clamp(P(t, tShow, tShow + 1.2));
      c.save(); c.globalAlpha = clamp(q) * (1 - feed * .9);
      rr(c, x + 40 + (520 - fw) / 2, fy, fw, fh, 10); c.fillStyle = hexA(pn.col, .14 + (n > 5000 ? .1 : 0)); c.fill(); c.strokeStyle = hexA(pn.col, .7); c.lineWidth = 1.5; c.stroke();
      if (n > 5000) for (let k = 0; k < 14; k++) { c.fillStyle = hexA(pn.col, .25); c.fillRect(x + 64, fy + 46 + k * 18, 300 + hash(k) * 160, 5); }
      c.restore();
      txt(c, s, x + 60, fy + 28, { size: 20, w: 600, a: clamp(q) * (1 - feed) });
      txt(c, fmt(n), x + 540, fy + 28, { size: 18, w: 600, f: F.mono, align: 'right', color: pn.col, a: clamp(q) * (1 - feed) });
    });
    // model chip
    const mx = x + 300, my = y + 640;
    glowDot(c, mx, my - 20, 120, pn.col, .2 + feed * .4 * (1 - P(t, S.at(4) + 1.6, S.at(4) + 2.4)));
    rr(c, mx - 70, my - 50, 140, 56, 14); c.fillStyle = '#0b1020'; c.fill(); c.strokeStyle = pn.col; c.lineWidth = 2; c.stroke();
    txt(c, 'MODEL', mx, my - 13, { size: 20, w: 700, f: F.mono, ls: 4, align: 'center', color: pn.col });
    // token counter + cost
    const cx = x + 590;
    txt(c, 'INPUT TOKENS', cx, y + 190, { size: 15, w: 700, f: F.mono, ls: 3, color: DIM });
    txt(c, fmt(Math.min(pn.total, shownTok)), cx, y + 240, { size: 44, w: 700, f: F.mono, color: '#fff' });
    const ra = P(t, S.at(4) + 1, S.at(4) + 1.8);
    txt(c, 'COST / 1K REQUESTS*', cx, y + 310, { size: 15, w: 700, f: F.mono, ls: 3, color: DIM, a: ra });
    txt(c, pn.cost, cx, y + 360, { size: 44, w: 700, f: F.mono, color: pn.col, a: ra });
    txt(c, 'RESPONSE', cx, y + 430, { size: 15, w: 700, f: F.mono, ls: 3, color: DIM, a: ra });
    pill(c, pi ? 'FASTER' : 'SLOWER', cx, y + 466, pn.col, { size: 16, a: ra });
    // output reply
    const oa = P(t, S.at(4) + 1.8, S.at(4) + 2.6);
    glass(c, cx - 10, y + 520, 220, 120, { acc: GOOD, a: oa, r: 14 });
    check(c, cx + 30, y + 580, 40, GOOD, oa);
    txt(c, 'Reply', cx + 66, y + 572, { size: 22, w: 600, a: oa }); txt(c, 'drafted', cx + 66, y + 600, { size: 22, w: 600, a: oa });
  });
  // big stat
  const ba = P(t, S.at(4) + 2.4, S.at(4) + 3);
  if (ba > 0) {
    c.save(); c.translate(990 + 300, 400); const s = lerp(1.4, 1, E.out(ba)); c.scale(s, s);
    glass(c, -170, -90, 340, 180, { acc: GOOD, a: ba, fill: .2 });
    txt(c, '−91%', 0, 18, { size: 76, w: 700, f: F.head, align: 'center', color: GOOD, a: ba });
    txt(c, 'INPUT TOKENS', 0, 62, { size: 16, w: 700, f: F.mono, ls: 4, align: 'center', a: ba });
    c.restore();
  }
  txt(c, '* illustrative price: $3 per million input tokens · same answer quality in both workflows', W / 2, 890, { size: 17, f: F.mono, align: 'center', color: DIM, a: P(t, S.at(4) + 1, S.at(4) + 2) * (1 - P(t, S.at(5) - .3, S.at(5))) });
  // technique chips + Nova (line 5)
  const na = P(t, S.at(5) - .4, S.at(5) + .4);
  if (na > 0) {
    c.save(); c.fillStyle = `rgba(6,4,2,${.86 * na})`; c.fillRect(0, 0, W, H); c.restore();
    person(c, 'NOVA', 300, 1000, 1.05, { t, amp: S.amp('NOVA'), stage: 1, look: .6, a: na });
    kinetic(c, 'BETTER CONTEXT > MORE CONTEXT', W / 2 + 120, 360, P(t, S.at(5) + .2, S.at(5) + 1.4), { size: 58, w: 700, f: F.head, ls: 3, align: 'center', color: '#ffd9a0' });
    ['Retrieve only what is relevant', 'Summarize long history', 'Write concise instructions', 'Cache repeated prompts', 'Right-size the model'].forEach((s, i) => {
      const ti = S.at(5) + .6 + i * .25; pill(c, s, 620 + (i % 3) * 400, 480 + Math.floor(i / 3) * 74, '#ffb547', { size: 20, a: P(t, ti, ti + .4) });
    });
  }
};

// ============================================================== CH4 — RAG
const DOCS = [['Handbook.pdf', '#3df5b0'], ['Policies.docx', '#7ab8ff'], ['Wiki pages', '#ffb547']];
const VPTS = Array.from({ length: 70 }, (_, i) => [(hash(i) - .5) * 300, (hash(i + 1) - .5) * 220, (hash(i + 2) - .5) * 300, i % 3]);
const NEAR = [5, 17, 41];
SCENES.rag = (c, S) => {
  const t = S.t;
  // ---- line 0: frozen knowledge (Lin)
  const ia = 1 - P(t, S.at(1) - .3, S.at(1) + .4);
  if (ia > 0) {
    c.save(); c.globalAlpha = ia;
    person(c, 'LIN', 420, 960, 1.35, { t, amp: S.amp('LIN'), look: .6, tablet: true });
    tag(c, 470, 380, 640, 290, 'DR. LIN · AI RESEARCHER', '#3df5b0', P(t, .3, 1.1));
    // knowledge timeline
    const x0 = 860, y0 = 470, x1 = 1760;
    glowLine(c, [[x0, y0], [lerp(x0, 1450, E.out(P(t, .4, 2))), y0]], '#3df5b0', 1, 3);
    txt(c, 'WHAT THE MODEL LEARNED', x0, y0 - 40, { size: 18, w: 700, f: F.mono, ls: 4, color: '#3df5b0' });
    const fa = P(t, 1.8, 2.6);
    c.globalAlpha = ia * fa; c.strokeStyle = '#bfe8ff'; c.lineWidth = 3;
    for (let k = 0; k < 6; k++) { const an = k * Math.PI / 3; c.beginPath(); c.moveTo(1450, y0); c.lineTo(1450 + Math.cos(an) * 34, y0 + Math.sin(an) * 34); c.stroke(); }
    c.globalAlpha = ia;
    txt(c, 'TRAINING ENDS', 1450, y0 + 80, { size: 18, w: 700, f: F.mono, ls: 3, align: 'center', color: '#bfe8ff', a: fa });
    c.setLineDash([6, 10]); c.strokeStyle = hexA('#ffffff', .3 * fa); c.lineWidth = 2; c.beginPath(); c.moveTo(1490, y0); c.lineTo(x1, y0); c.stroke(); c.setLineDash([]);
    // your docs bounce
    const da = P(t, S.at(0) + 3, S.at(0) + 4);
    ['Your docs', 'Your policies', 'Your data'].forEach((s, i) => pill(c, s, 1620, 580 + i * 62, '#ffb547', { size: 18, align: 'center', a: da * P(t, S.at(0) + 3 + i * .3, S.at(0) + 3.5 + i * .3) }));
    txt(c, 'never seen', 1620, 790, { size: 20, align: 'center', color: DIM, a: da });
    c.restore();
  }
  const pa = P(t, S.at(1) - .2, S.at(1) + .6);
  const dim = 1 - .85 * P(t, S.at(5) - .4, S.at(5) + .3);
  if (pa > 0) {
    c.save(); c.globalAlpha = pa * dim;
    // step chips
    const steps = ['1  CHUNK', '2  EMBED + STORE', '3  SEARCH', '4  AUGMENT PROMPT', '5  GENERATE + CITE'];
    let sx = 260; const cur = S.cur();
    steps.forEach((s, i) => { const on = i + 1 <= cur; sx += pill(c, s, sx, 190, '#3df5b0', { size: 15, solid: i + 1 === cur, a: on ? 1 : .35, tc: on ? TXT : DIM }) + 16; });
    // docs
    DOCS.forEach(([s, col], i) => {
      const y = 290 + i * 170; const q = E.out(P(t, S.at(1) + .3 + i * .2, S.at(1) + 1 + i * .2));
      glass(c, 90, y, 200, 130, { acc: col, a: q, r: 12 });
      for (let k = 0; k < 4; k++) { c.fillStyle = hexA(col, .4 * q); c.fillRect(110, y + 46 + k * 16, 150 - k * 18, 5); }
      txt(c, s, 110, y + 32, { size: 18, w: 700, f: F.mono, color: col, a: q });
    });
    // chunks fly to DB
    const cp = P(t, S.at(1) + 2.6, S.at(1) + 6.5);
    for (let i = 0; i < 12; i++) {
      const d = Math.floor(i / 4), k = i % 4; const q = E.io(clamp(cp * 2 - i * .07));
      const x0 = 330 + k * 46, y0 = 330 + d * 170, x1 = 620, y1 = 540;
      const x = lerp(x0, x1, P(q, .5, 1)), y = lerp(y0, y1, P(q, .5, 1));
      c.globalAlpha = pa * dim * clamp(cp * 6 - i * .2) * (1 - P(q, .9, 1));
      rr(c, x, y, 38, 26, 6); c.fillStyle = hexA(DOCS[d][1], .35); c.fill(); c.strokeStyle = DOCS[d][1]; c.lineWidth = 1.2; c.stroke();
    }
    c.globalAlpha = pa * dim;
    txt(c, 'chunks', 420, 860, { size: 18, f: F.mono, color: DIM, a: P(t, S.at(1) + 2.6, S.at(1) + 3) });
    // vector DB cylinder
    const dbx = 880, dby = 560;
    const ca = P(t, S.at(1) + 4, S.at(1) + 5);
    c.globalAlpha = pa * dim * ca;
    c.strokeStyle = hexA('#3df5b0', .7); c.lineWidth = 2;
    c.beginPath(); c.ellipse(dbx, dby - 210, 200, 46, 0, 0, 7); c.stroke();
    c.beginPath(); c.moveTo(dbx - 200, dby - 210); c.lineTo(dbx - 200, dby + 200); c.ellipse(dbx, dby + 200, 200, 46, 0, Math.PI, 0, true); c.lineTo(dbx + 200, dby - 210); c.stroke();
    c.fillStyle = hexA('#3df5b0', .05); c.fillRect(dbx - 200, dby - 210, 400, 410);
    txt(c, 'VECTOR DATABASE', dbx, dby + 310, { size: 17, w: 700, f: F.mono, ls: 4, align: 'center', color: '#3df5b0' });
    const cam = { yaw: t * .3, pitch: .3, dist: 900, cx: dbx, cy: dby, f: 900 };
    const VP = VPTS.map(v => proj(v[0], v[1], v[2], cam));
    const sp = P(t, S.at(2) + 1.8, S.at(2) + 3.4);
    VP.forEach(([x, y, f], i) => {
      const n = NEAR.includes(i); const pp = clamp(ca * 2 - i / 70);
      c.fillStyle = hexA(n && sp > 0 ? '#ffffff' : DOCS[VPTS[i][3]][1], (.4 + .5 * f) * pp); c.beginPath(); c.arc(x, y, (n && sp > 0 ? 7 : 4) * f, 0, 7); c.fill();
    });
    // query
    const qa = P(t, S.at(2), S.at(2) + .7);
    if (qa > 0) {
      c.globalAlpha = pa * dim * qa;
      glass(c, 600, 250, 760, 80, { acc: '#7ab8ff', r: 16 });
      txt(c, 'How many vacation days do new employees get?', 630, 300, { size: 26, w: 600 });
      const qp = E.io(P(t, S.at(2) + .8, S.at(2) + 1.8));
      const qx = lerp(980, dbx + 20, qp), qy = lerp(340, dby - 10, qp);
      glowDot(c, qx, qy, 40, '#7ab8ff', 1); c.fillStyle = '#fff'; c.beginPath(); c.arc(qx, qy, 8, 0, 7); c.fill();
      if (sp > 0) NEAR.forEach((ni, k) => { const [x, y] = VP[ni]; glowLine(c, [[qx, qy], [lerp(qx, x, sp), lerp(qy, y, sp)]], '#ffffff', .8, 1.5); txt(c, ['0.91', '0.87', '0.82'][k], x + 12, y - 8, { size: 16, f: F.mono, a: sp }); });
      pill(c, 'TOP-3 CLOSEST IN MEANING', dbx, dby + 262, '#ffffff', { size: 15, align: 'center', a: sp });
    }
    // prompt card
    const pc = P(t, S.at(3), S.at(3) + .6);
    if (pc > 0) {
      c.globalAlpha = pa * dim * pc;
      glass(c, 1180, 380, 650, 300, { acc: '#3df5b0' });
      txt(c, 'PROMPT', 1210, 420, { size: 16, w: 700, f: F.mono, ls: 5, color: '#3df5b0' });
      ['§3.1  New employees receive 20 days of paid…', '§3.4  Leave requests are submitted…', '§3.6  Unused days carry over…'].forEach((s, k) => {
        const q = E.out(P(t, S.at(3) + .4 + k * .35, S.at(3) + 1.2 + k * .35));
        const [vx, vy] = VP[NEAR[k]];
        const x = lerp(vx, 1210, q), y = lerp(vy, 450 + k * 52, q);
        rr(c, x, y, 590 * q + 20, 40, 8); c.fillStyle = hexA('#3df5b0', .12); c.fill(); c.strokeStyle = hexA('#3df5b0', .6); c.lineWidth = 1.2; c.stroke();
        txt(c, s, x + 14, y + 27, { size: 18, f: F.mono, a: q });
      });
      txt(c, 'Question: How many vacation days do new employees get?', 1210, 640, { size: 18, f: F.mono, color: '#bcd6ff', a: P(t, S.at(3) + 1.8, S.at(3) + 2.3) });
    }
    // answer
    const aa = P(t, S.at(4), S.at(4) + .6);
    if (aa > 0) {
      c.globalAlpha = pa * dim * aa;
      flow(c, 1500, 690, 1500, 735, t, aa, '#3df5b0');
      glass(c, 1180, 745, 650, 140, { acc: '#3df5b0', fill: .16 });
      para(c, typed('New employees get 20 days of paid leave per year.', P(t, S.at(4) + .3, S.at(4) + 2)), 1210, 795, 600, { size: 24, w: 600 });
      pill(c, '📎 Handbook §3.1', 1210, 850, '#3df5b0', { size: 16, a: P(t, S.at(4) + 2, S.at(4) + 2.5) * (0.85 + .15 * Math.sin(t * 6)), f: F.mono });
    }
    c.restore();
  }
  // ---- lines 5-6: Nova + Lin conversation
  const ca2 = P(t, S.at(5) - .4, S.at(5) + .3);
  if (ca2 > 0) {
    person(c, 'NOVA', 330, 1010, 1.05, { t, amp: S.amp('NOVA'), stage: 2, look: .7, a: ca2 });
    person(c, 'LIN', 1600, 1010, 1.05, { t, amp: S.amp('LIN'), look: -.7, a: ca2 });
    kinetic(c, 'NO RETRAINING.', W / 2, 330, P(t, S.at(6), S.at(6) + 1), { size: 64, w: 700, f: F.head, ls: 6, align: 'center', color: '#3df5b0' });
    kinetic(c, 'JUST THE RIGHT CONTEXT.', W / 2, 410, P(t, S.at(6) + .5, S.at(6) + 1.5), { size: 44, w: 600, f: F.head, ls: 6, align: 'center' });
  }
};

// ============================================================== CH5 — AGENTS
const AG = [['PLANNER', '#4de8ff', -1, -1], ['RESEARCHER', '#3df5b0', 1, -1], ['BUILDER', '#ffb547', 1, 1], ['REVIEWER', '#ff5fa2', -1, 1]];
const TOOLS = [['DATABASE', 1, 'RESEARCHER'], ['CODE', 2, 'BUILDER'], ['EMAIL', 3, 'REVIEWER']];
SCENES.agents = (c, S) => {
  const t = S.t;
  // line 0: Kai + chatbot vs agent
  const ia = 1 - P(t, S.at(1) - .3, S.at(1) + .4);
  if (ia > 0) {
    c.save(); c.globalAlpha = ia;
    person(c, 'KAI', 470, 960, 1.35, { t, amp: S.amp('KAI'), look: .6 });
    tag(c, 520, 380, 700, 290, 'KAI · AUTOMATION SPECIALIST', '#ff5fa2', P(t, .2, 1));
    const p1 = P(t, S.at(0), S.at(0) + .8), p2 = P(t, S.at(0) + 1.1, S.at(0) + 1.9);
    glass(c, 960, 330, 380, 300, { acc: '#7a86a8', a: p1 }); glass(c, 1400, 330, 380, 300, { acc: '#ff5fa2', a: p2, fill: .18 });
    txt(c, 'CHATBOT', 1150, 400, { size: 22, w: 700, f: F.mono, ls: 6, align: 'center', color: DIM, a: p1 });
    txt(c, 'answers', 1150, 520, { size: 54, w: 600, f: F.head, align: 'center', color: '#b9c2dc', a: p1 });
    txt(c, 'AGENT', 1590, 400, { size: 22, w: 700, f: F.mono, ls: 6, align: 'center', color: '#ff5fa2', a: p2 });
    kinetic(c, 'acts', 1590, 520, p2, { size: 64, w: 700, f: F.head, align: 'center', color: '#fff' });
    c.restore();
  }
  // line 1: the loop
  const la = P(t, S.at(1) - .2, S.at(1) + .6) * (1 - P(t, S.at(2) - .2, S.at(2) + .6));
  if (la > 0) {
    const cx = W / 2, cy = 520, R = 250;
    c.save(); c.globalAlpha = la;
    c.beginPath(); c.arc(cx, cy, R, 0, 7); c.strokeStyle = hexA('#ff5fa2', .3); c.lineWidth = 3; c.stroke();
    const ang = -Math.PI / 2 + (t - S.at(1)) * 1.4;
    for (let k = 0; k < 18; k++) glowDot(c, cx + Math.cos(ang - k * .04) * R, cy + Math.sin(ang - k * .04) * R, 26 - k, '#ff5fa2', 1 - k / 18);
    const nodes = [['PLAN', 'next step'], ['ACT', 'call a tool'], ['OBSERVE', 'read the result'], ['DECIDE', 'continue or stop']];
    nodes.forEach(([s, d], i) => {
      const a = -Math.PI / 2 + i * Math.PI / 2; const x = cx + Math.cos(a) * R, y = cy + Math.sin(a) * R;
      const near = Math.cos(ang - a) > .92;
      const q = P(t, S.at(1) + 1 + i * 1.2, S.at(1) + 1.6 + i * 1.2);
      glass(c, x - 120, y - 50, 240, 100, { acc: '#ff5fa2', a: q, fill: near ? .25 : .1, r: 18 });
      txt(c, s, x, y - 2, { size: 30, w: 700, f: F.head, align: 'center', a: q, color: near ? '#fff' : '#ffc2dc' });
      txt(c, d, x, y + 30, { size: 18, align: 'center', color: DIM, a: q });
    });
    glowDot(c, cx, cy, 130, '#ff5fa2', .4); txt(c, 'MODEL', cx, cy + 10, { size: 26, w: 700, f: F.mono, ls: 6, align: 'center' });
    c.restore();
  }
  // lines 2-4: multi-agent isometric world
  const wa = P(t, S.at(2) - .2, S.at(2) + .8);
  if (wa > 0) {
    const o = { cx: 800, cy: 560, k: .85 };
    c.save(); c.globalAlpha = wa;
    for (let i = -5; i <= 5; i++) { const a1 = iso(i * 70, -350, 0, o), b1 = iso(i * 70, 350, 0, o), a2 = iso(-350, i * 70, 0, o), b2 = iso(350, i * 70, 0, o); c.strokeStyle = hexA('#ff5fa2', .12); c.lineWidth = 1; c.beginPath(); c.moveTo(a1[0], a1[1]); c.lineTo(b1[0], b1[1]); c.moveTo(a2[0], a2[1]); c.lineTo(b2[0], b2[1]); c.stroke(); }
    // goal card
    glass(c, 1400, 170, 440, 96, { acc: '#ff5fa2', r: 16 });
    txt(c, 'GOAL', 1428, 206, { size: 15, w: 700, f: F.mono, ls: 4, color: '#ff5fa2' });
    txt(c, 'Weekly sales report → email team', 1428, 244, { size: 23, w: 600 });
    const pos = AG.map(a => iso(a[2] * 190, a[3] * 190, 0, o));
    // tool stations
    TOOLS.forEach(([s, ai]) => { const [x, y] = iso(AG[ai][2] * 300, AG[ai][3] * 300, 0, o); const used = P(t, S.at(3) + ai * 1.5, S.at(3) + ai * 1.5 + .4);
      isoBox(c, AG[ai][2] * 300 - 35, AG[ai][3] * 300 - 35, 0, 70, 70, 40, o, [hexA(AG[ai][1], .25 + used * .5), hexA(AG[ai][1], .15), hexA(AG[ai][1], .1)], P(t, S.at(3) - .5, S.at(3)));
      txt(c, s, x, y + 46, { size: 15, w: 700, f: F.mono, ls: 3, align: 'center', color: AG[ai][1], a: P(t, S.at(3) - .5, S.at(3)) });
      if (used > 0 && used < 1) glowDot(c, x, y - 30, 80, AG[ai][1], 1 - used);
    });
    // packets during line 3
    const seq = [[0, 1], [1, 2], [2, 3]];
    const seg = (S.end(3) - S.at(3) - .5) / 4;
    seq.forEach(([a, b], k) => { const q = P(t, S.at(3) + k * seg + .2, S.at(3) + (k + 1) * seg); if (q > 0 && q < 1) { const x = lerp(pos[a][0], pos[b][0], E.io(q)), y = lerp(pos[a][1], pos[b][1], E.io(q)) - 110 - Math.sin(q * Math.PI) * 80; glowDot(c, x, y, 34, AG[b][1], 1); rr(c, x - 14, y - 10, 28, 20, 4); c.fillStyle = '#fff'; c.fill(); } });
    // bots
    AG.forEach(([s, col], i) => {
      const ti = S.at(2) + 2 + i * 1.9; const q = E.back(P(t, ti, ti + .6));
      const active = t > S.at(3) + i * seg && t < S.at(3) + (i + 1) * seg + .3;
      bot(c, pos[i][0], pos[i][1] - (1 - q) * 60, .85, col, { t, a: clamp(q), active });
      tag(c, pos[i][0], pos[i][1] - 200, pos[i][0] + (AG[i][2] > 0 ? 80 : -80), pos[i][1] - 240, s, col, P(t, ti + .3, ti + 1));
    });
    // checklist
    const items = ['Plan the report', 'Pull sales data', 'Build chart + summary', 'Review numbers', 'Email the team'];
    glass(c, 1400, 300, 440, 420, { acc: '#ff5fa2', a: P(t, S.at(3) - .4, S.at(3) + .2) });
    txt(c, 'TASK PROGRESS', 1430, 345, { size: 16, w: 700, f: F.mono, ls: 4, color: '#ff5fa2', a: P(t, S.at(3) - .4, S.at(3) + .2) });
    items.forEach((s, i) => {
      const done = P(t, S.at(3) + .4 + i * (S.end(3) - S.at(3)) / 5.2, S.at(3) + .9 + i * (S.end(3) - S.at(3)) / 5.2);
      const a = P(t, S.at(3) - .2, S.at(3) + .4);
      rr(c, 1430, 380 + i * 58, 30, 30, 8); c.strokeStyle = hexA(done > 0 ? GOOD : '#ffffff', .6 * a); c.lineWidth = 2; c.stroke();
      if (done > 0) check(c, 1445, 395 + i * 58, 26, GOOD, done);
      txt(c, s, 1476, 403 + i * 58, { size: 21, a, color: done >= 1 ? '#fff' : '#9aa6c2' });
    });
    const ta = P(t, S.end(3) - .3, S.end(3) + .3);
    if (ta > 0) pill(c, '✓ TASK COMPLETE', 1620, 680, GOOD, { size: 18, align: 'center', solid: true, a: ta });
    c.restore();
  }
  // line 4: Kai + guardrails
  const ka = P(t, S.at(4) - .3, S.at(4) + .4);
  if (ka > 0) {
    c.save(); c.fillStyle = `rgba(6,3,8,${.85 * ka})`; c.fillRect(0, 0, W, H); c.restore();
    person(c, 'KAI', 300, 1010, 1.05, { t, amp: S.amp('KAI'), look: .7, a: ka });
    [['CLEAR INSTRUCTIONS', 1.2], ['THE RIGHT TOOLS', 2.6], ['FIRM LIMITS', 3.8]].forEach(([s, d], i) => {
      const q = E.back(P(t, S.at(4) + d, S.at(4) + d + .5));
      glass(c, 620 + i * 420, 380 + (1 - q) * 40, 380, 150, { acc: '#ff5fa2', a: clamp(q), fill: .16 });
      txt(c, String(i + 1).padStart(2, '0'), 650 + i * 420, 430, { size: 18, w: 700, f: F.mono, color: '#ff5fa2', a: clamp(q) });
      txt(c, s, 650 + i * 420, 490, { size: 30, w: 700, f: F.head, a: clamp(q) });
    });
  }
};
SCENES.challenge = (c, S) => {
  const t = S.t, acc = S.acc;
  quizHeader(c, S, 'AGENT PERMISSIONS CHALLENGE', acc);
  txt(c, 'Which actions can an agent take on its own?', W / 2, 300, { size: 40, w: 600, f: F.head, align: 'center', a: P(t, S.at(0) + .3, S.at(0) + 1) });
  const rev = P(t, S.at(1), S.at(1) + .5);
  const cards = [['Draft an email for review', 'low risk · reversible', true], ['Search internal documents', 'read-only', true], ['Issue a $5,000 refund', 'costly', false], ['Delete customer records', 'irreversible', false]];
  cards.forEach(([s, d, ok], i) => {
    const x = W / 2 - 620 + (i % 2) * 640, y = 360 + Math.floor(i / 2) * 230;
    const q = E.back(P(t, S.at(0) + 1 + i * .3, S.at(0) + 1.6 + i * .3));
    const col = rev ? (ok ? GOOD : WARN) : acc;
    const r2 = P(t, S.at(1) + (ok ? .2 : 2.6) + (i % 2) * .4, S.at(1) + (ok ? .7 : 3.1) + (i % 2) * .4);
    glass(c, x, y + (1 - q) * 40, 600, 190, { acc: r2 > 0 ? col : acc, a: clamp(q), fill: .08 + r2 * .1 });
    txt(c, s, x + 40, y + 78, { size: 32, w: 600, f: F.head, a: clamp(q) });
    txt(c, d.toUpperCase(), x + 40, y + 118, { size: 16, w: 600, f: F.mono, ls: 3, color: DIM, a: clamp(q) });
    if (r2 > 0) pill(c, ok ? '✓ AUTOMATE' : '⚠ HUMAN APPROVAL', x + 40, y + 155, ok ? GOOD : WARN, { size: 16, solid: true, a: r2 });
  });
  txt(c, 'Rule of thumb: automate the reversible · approve the irreversible', W / 2, 875, { size: 22, w: 500, align: 'center', color: '#ffc2dc', a: P(t, S.at(1) + 5, S.at(1) + 6) });
};

// ============================================================== CH6 — PROBLEM SOLVER
function bakery(c, x, y, k, t, a = 1) {
  const o = { cx: x, cy: y, k };
  isoBox(c, -180, -140, 0, 360, 280, 230, o, ['#5a3a3a', '#3b2228', '#2b1820'], a);
  // awning stripes
  for (let i = 0; i < 8; i++) isoBox(c, -180 + i * 45, 140, 170, 45, 40, 14, o, [i % 2 ? '#ff8a5c' : '#fff1e6', i % 2 ? '#c4562f' : '#d9c8bb', '#a04020'], a);
  // windows glow
  c.save(); c.globalAlpha = a;
  const wp = [iso(-140, 140, 30, o), iso(-20, 140, 30, o), iso(-20, 140, 140, o), iso(-140, 140, 140, o)];
  c.beginPath(); wp.forEach((q, i) => i ? c.lineTo(q[0], q[1]) : c.moveTo(q[0], q[1])); c.closePath(); c.fillStyle = 'rgba(255,200,120,0.75)'; c.fill();
  const dp = [iso(40, 140, 0, o), iso(130, 140, 0, o), iso(130, 140, 140, o), iso(40, 140, 140, o)];
  c.beginPath(); dp.forEach((q, i) => i ? c.lineTo(q[0], q[1]) : c.moveTo(q[0], q[1])); c.closePath(); c.fillStyle = '#1a0f12'; c.fill();
  const [sx, sy] = iso(-20, 140, 250, o);
  c.restore();
  glowDot(c, iso(-80, 140, 80, o)[0], iso(-80, 140, 80, o)[1], 160 * k, '#ffb070', .35 * a);
  txt(c, "MAYA'S BAKERY", sx, sy, { size: 26 * k, w: 700, f: F.head, ls: 4, align: 'center', color: '#ffd9c4', a, glow: 12, glowColor: '#ff8a5c' });
}
SCENES.problem = (c, S) => {
  const t = S.t;
  const phaseA = 1 - P(t, S.at(2) - .3, S.at(2) + .5);
  if (phaseA > 0) {
    c.save(); c.globalAlpha = phaseA;
    bakery(c, 960, 800, .8, t);
    person(c, 'MAYA', 330, 980, 1.25, { t, amp: S.amp('MAYA'), look: .6 });
    tag(c, 380, 420, 470, 620, 'MAYA · BAKERY OWNER', '#ff8a5c', P(t, .2, 1));
    // inbox
    glass(c, 700, 150, 520, 300, { acc: BAD, a: P(t, .3, 1) });
    txt(c, 'INBOX', 730, 195, { size: 16, w: 700, f: F.mono, ls: 4, color: '#ff9aa9' });
    const n = Math.floor(lerp(0, 112, E.out(P(t, .5, S.at(1)))));
    txt(c, `UNANSWERED: ${n}`, 1190, 195, { size: 18, w: 700, f: F.mono, align: 'right', color: BAD });
    const msgs = ['Open on Sunday?', 'Is the cake nut-free?', 'Where is my order?', 'Gluten-free options?', 'Open on Sunday??', 'Order #4471 status?'];
    msgs.forEach((m, i) => { const q = E.back(P(t, .6 + i * .55, 1 + i * .55)); const y = 225 + (i % 4) * 52 + (i >= 4 ? 26 : 0); const x = 730 + (i >= 4 ? 230 : 0);
      if (q > 0) { rr(c, x, y, 220, 40, 14); c.fillStyle = hexA('#ff5470', .14 * clamp(q)); c.fill(); c.strokeStyle = hexA('#ff5470', .5 * clamp(q)); c.lineWidth = 1.2; c.stroke(); txt(c, m, x + 14, y + 26, { size: 17, a: clamp(q) }); } });
    // Sam
    const sa = P(t, S.at(1) - .3, S.at(1) + .4);
    if (sa > 0) {
      person(c, 'SAM', 1600, 980, 1.25, { t, amp: S.amp('SAM'), look: -.6, a: sa });
      tag(c, 1560, 420, 1440, 620, 'SAM · CUSTOMER', '#3df5b0', P(t, S.at(1), S.at(1) + .8));
      glass(c, 1340, 160, 470, 160, { acc: '#3df5b0', a: sa, r: 18 });
      txt(c, 'Is the carrot cake nut-free?', 1370, 215, { size: 24, w: 600, a: sa });
      txt(c, 'Delivered · no reply · 3 h', 1370, 255, { size: 18, f: F.mono, color: DIM, a: sa });
      pill(c, 'ORDERED ELSEWHERE', 1370, 292, BAD, { size: 15, solid: true, a: P(t, S.at(1) + 3, S.at(1) + 3.5) });
    }
    c.restore();
  }
  // line 2: Nova diagnoses
  const da = P(t, S.at(2) - .3, S.at(2) + .5) * (1 - P(t, S.at(3) - .3, S.at(3) + .3));
  if (da > 0) {
    c.save(); c.globalAlpha = da;
    person(c, 'NOVA', 470, 960, 1.35, { t, amp: S.amp('NOVA'), stage: 3, look: .6 });
    kinetic(c, 'NOT A TECHNOLOGY PROBLEM.', 820, 330, P(t, S.at(2) + 1, S.at(2) + 2), { size: 44, w: 700, f: F.head, ls: 3, color: '#9aa6c2' });
    kinetic(c, 'A BUSINESS PROBLEM.', 820, 410, P(t, S.at(2) + 2.4, S.at(2) + 3.2), { size: 60, w: 700, f: F.head, ls: 3, color: '#ff8a5c' });
    [['LOST ORDERS', BAD, 4.6], ['OVERWHELMED TEAM', WARN, 5.6]].forEach(([s, col, d], i) => {
      const q = E.back(P(t, S.at(2) + d, S.at(2) + d + .5));
      glass(c, 820 + i * 460, 480, 420, 140, { acc: col, a: clamp(q) });
      txt(c, s, 850 + i * 460, 560, { size: 30, w: 700, f: F.head, color: col, a: clamp(q) });
    });
    c.restore();
  }
  // line 3: blueprint
  const ba = P(t, S.at(3) - .3, S.at(3) + .5);
  if (ba > 0) {
    c.save(); c.globalAlpha = ba;
    c.fillStyle = 'rgba(8,24,52,0.85)'; c.fillRect(0, 0, W, H);
    c.strokeStyle = 'rgba(120,180,255,0.10)'; c.lineWidth = 1;
    for (let x = 0; x < W; x += 40) { c.beginPath(); c.moveTo(x, 0); c.lineTo(x, H); c.stroke(); }
    for (let y = 0; y < H; y += 40) { c.beginPath(); c.moveTo(0, y); c.lineTo(W, y); c.stroke(); }
    txt(c, 'SOLUTION BLUEPRINT · v1', 90, 220, { size: 18, w: 700, f: F.mono, ls: 5, color: '#9cc8ff' });
    const node = (x, y, w, s, sub, col, d) => { const q = E.out(P(t, S.at(3) + d, S.at(3) + d + .6)); c.save(); c.globalAlpha *= q; c.setLineDash([]); rr(c, x - w / 2, y - 50, w, 100, 14); c.fillStyle = hexA(col, .1); c.fill(); c.strokeStyle = col; c.lineWidth = 2; c.stroke(); c.restore(); txt(c, s, x, y - 2, { size: 26, w: 700, f: F.head, align: 'center', a: q * ba }); txt(c, sub, x, y + 30, { size: 16, f: F.mono, align: 'center', color: DIM, a: q * ba }); };
    const line = (x1, y1, x2, y2, d, dash) => { const q = E.io(P(t, S.at(3) + d, S.at(3) + d + .8)); c.save(); if (dash) c.setLineDash([10, 8]); c.strokeStyle = '#9cc8ff'; c.lineWidth = 2; c.beginPath(); c.moveTo(x1, y1); c.lineTo(lerp(x1, x2, q), lerp(y1, y2, q)); c.stroke(); c.restore(); if (q >= 1) arrowHead(c, x2, y2, Math.atan2(y2 - y1, x2 - x1), '#9cc8ff', ba); };
    node(360, 540, 260, 'Customer', 'web · chat · SMS', '#3df5b0', .4);
    node(960, 540, 320, 'AI Assistant', 'grounded answers', '#ff8a5c', 1.4);
    node(960, 300, 380, 'Menu + Policies', 'knowledge base (RAG)', '#7ab8ff', 3.6);
    node(1560, 540, 280, 'Order System', 'live status', '#ffb547', 6.2);
    node(960, 790, 320, 'Staff Handoff', 'anything unusual', '#ff5fa2', 8.6);
    line(490, 540, 795, 540, 1, false); line(960, 350, 960, 485, 4.2, false); line(1125, 540, 1415, 540, 6.8, false); line(960, 595, 960, 735, 9.2, true);
    person(c, 'NOVA', 1650, 1000, .8, { t, stage: 3, look: -.6, a: ba });
    c.restore();
  }
};
SCENES.ship = (c, S) => {
  const t = S.t;
  // line 0: test harness
  const ta = 1 - P(t, S.at(1) - .3, S.at(1) + .2);
  if (ta > 0) {
    c.save(); c.globalAlpha = ta;
    glass(c, 140, 200, 700, 680, { acc: '#ff8a5c' });
    txt(c, 'EVALUATION · 100 REAL QUESTIONS', 175, 245, { size: 17, w: 700, f: F.mono, ls: 3, color: '#ff8a5c' });
    const run = P(t, .4, S.at(0) + 3.6), fix = P(t, S.at(0) + 4.2, S.end(0));
    let pass = 0;
    for (let i = 0; i < 100; i++) {
      const x = 180 + (i % 10) * 62, y = 280 + Math.floor(i / 10) * 56;
      const shown = run * 100 > i; const bad = hash(i * 3.3) < .13; const fixed = bad && fix * 13 > (i % 13);
      const col = !shown ? '#2a3046' : bad && !fixed ? BAD : GOOD;
      if (shown && (!bad || fixed)) pass++;
      rr(c, x, y, 48, 42, 8); c.fillStyle = hexA(col, shown ? .55 : 1); c.fill();
    }
    txt(c, `PASSED ${pass} / 100`, 175, 860, { size: 26, w: 700, f: F.mono, color: pass === 100 ? GOOD : '#fff' });
    person(c, 'NOVA', 1300, 960, 1.35, { t, stage: 3, look: -.6 });
    pill(c, fix > 0 ? 'FIXING WRONG ANSWERS…' : 'RUNNING TESTS…', 1300, 300, fix >= 1 ? GOOD : '#ff8a5c', { size: 18, align: 'center' });
    c.restore();
  }
  // line 1: ship!
  const sa = P(t, S.at(1) - .2, S.at(1) + .3);
  if (sa > 0) {
    const flash = Math.max(0, 1 - Math.abs(t - S.at(1) - .1) * 3);
    const toLeft = E.io(P(t, S.at(2) - .5, S.at(2) + .5));
    const px = lerp(W / 2 - 200, 200, toLeft), py = lerp(180 + (1 - E.out(sa)) * 400, 200, toLeft);
    c.save(); c.globalAlpha = sa;
    glowDot(c, px + 200, py + 330, 500, '#ff8a5c', .3);
    rr(c, px, py, 400, 680, 46); c.fillStyle = '#0a0d16'; c.fill(); c.strokeStyle = '#ff8a5c'; c.lineWidth = 3; c.stroke();
    rr(c, px + 16, py + 16, 368, 648, 34); c.fillStyle = '#121828'; c.fill();
    txt(c, "Maya's Bakery · Assistant", px + 200, py + 70, { size: 18, w: 700, align: 'center', color: '#ffd9c4' });
    const b = (s, right, y, col, d) => { const q = E.out(P(t, S.at(1) + d, S.at(1) + d + .5)); const ls = wrap(c, s, 250, { size: 19 }); const h = ls.length * 26 + 22; const x = right ? px + 370 - 280 : px + 34; c.globalAlpha = sa * q; rr(c, x, y, 280, h, 16); c.fillStyle = col; c.fill(); ls.forEach((l, i) => txt(c, l, x + 14, y + 30 + i * 26, { size: 19, color: right ? '#06101c' : TXT })); c.globalAlpha = sa; };
    b('Is the carrot cake nut-free?', true, py + 110, '#3df5b0', .3);
    b("Yes — it's made without nuts, in our nut-free prep area. Want one for pickup tomorrow?", false, py + 190, '#2a3350', 1.2);
    b('Yes please, 2 pm!', true, py + 360, '#3df5b0', 2.6);
    b('Done ✓ Order #4512 confirmed for 2:00 pm pickup.', false, py + 430, '#2a3350', 3.6);
    pill(c, '📎 Allergen guide', px + 34, py + 560, '#7ab8ff', { size: 14, a: P(t, S.at(1) + 1.8, S.at(1) + 2.3), f: F.mono });
    c.restore();
    if (flash > 0) { c.save(); c.globalCompositeOperation = 'lighter'; c.fillStyle = `rgba(255,170,120,${flash * .5})`; c.fillRect(0, 0, W, H); c.restore(); }
    kinetic(c, 'SHIPPED.', W / 2 + 540, 520, P(t, S.at(1), S.at(1) + .6), { size: 110, w: 700, f: F.head, ls: 10, align: 'center', color: '#ff8a5c', a: 1 - toLeft });
  }
  // line 2: before/after dashboard + Maya
  const da = P(t, S.at(2) - .3, S.at(2) + .5) * (1 - .55 * P(t, S.at(3) - .3, S.at(3) + .3));
  if (da > 0) {
    c.save(); c.globalAlpha = da;
    bust(c, 'MAYA', 780, 300, 90, { t, amp: S.amp('MAYA'), look: .3 });
    txt(c, 'MAYA · BAKERY OWNER', 890, 290, { size: 15, w: 700, f: F.mono, ls: 3, color: '#ff8a5c' });
    txt(c, '“Hours to seconds.”', 890, 336, { size: 34, w: 600, f: F.head });
    const rows = [['Average reply time', '4 h 12 m', '8 s'], ['Messages left unanswered', '48 %', '2 %'], ['Staff hours on inbox / week', '21 h', '4 h']];
    glass(c, 700, 430, 1120, 400, { acc: '#ff8a5c' });
    txt(c, 'BEFORE', 1360, 485, { size: 15, w: 700, f: F.mono, ls: 4, align: 'center', color: DIM }); txt(c, 'AFTER', 1640, 485, { size: 15, w: 700, f: F.mono, ls: 4, align: 'center', color: GOOD });
    rows.forEach(([k, b4, af], i) => {
      const y = 560 + i * 92; const q = P(t, S.at(2) + .5 + i * .5, S.at(2) + 1.1 + i * .5);
      txt(c, k, 740, y, { size: 26, w: 500, a: q });
      txt(c, b4, 1360, y, { size: 32, w: 700, f: F.mono, align: 'center', color: '#ff9aa9', a: q });
      flow(c, 1440, y - 10, 1540, y - 10, t, q, GOOD, { n: 1 });
      txt(c, af, 1640, y, { size: 32, w: 700, f: F.mono, align: 'center', color: GOOD, a: P(t, S.at(2) + 1 + i * .5, S.at(2) + 1.5 + i * .5) });
    });
    pill(c, 'ILLUSTRATIVE SCENARIO', 1800, 800, '#9aa6c2', { size: 13, align: 'right' });
    c.restore();
  }
  // line 3: method
  const ma = P(t, S.at(3) - .2, S.at(3) + .5);
  if (ma > 0) {
    const steps = ['REAL PROBLEM', 'REAL DATA', 'TEST IT', 'HUMAN IN THE LOOP'];
    c.save(); c.fillStyle = `rgba(10,5,3,${.88 * ma})`; c.fillRect(0, 0, W, H); c.restore();
    steps.forEach((s, i) => {
      const q = E.back(P(t, S.at(3) + i * 1.5, S.at(3) + i * 1.5 + .5)); const x = 170 + i * 420;
      glass(c, x, 420 + (1 - q) * 30, 360, 170, { acc: '#ff8a5c', a: clamp(q), fill: .16 });
      txt(c, String(i + 1).padStart(2, '0'), x + 30, 470, { size: 20, w: 700, f: F.mono, color: '#ff8a5c', a: clamp(q) });
      txt(c, s, x + 30, 545, { size: 30, w: 700, f: F.head, a: clamp(q) });
      if (i < 3) flow(c, x + 365, 505, x + 415, 505, t, P(t, S.at(3) + i * 1.5 + .4, S.at(3) + i * 1.5 + .8), '#ff8a5c', { n: 1 });
    });
  }
};

// ============================================================== CH7 — TRUST
SCENES.trust = (c, S) => {
  const t = S.t;
  const ia = 1 - P(t, S.at(1) - .3, S.at(1) + .3);
  if (ia > 0) {
    c.save(); c.globalAlpha = ia;
    person(c, 'LIN', 420, 960, 1.35, { t, amp: S.amp('LIN'), look: .6, tablet: true });
    glass(c, 860, 300, 900, 420, { acc: '#7ab8ff' });
    txt(c, 'HALLUCINATION', 910, 400, { size: 22, w: 700, f: F.mono, ls: 8, color: '#7ab8ff' });
    [['confident', '#fff', .6, 0], ['fluent', '#fff', 1.4, 330], ['wrong.', BAD, 3, 580]].forEach(([w, col, d, dx], i) => kinetic(c, w, 910 + dx, 520, P(t, S.at(0) + d, S.at(0) + d + .6), { size: 64, w: 700, f: F.head, color: col }));
    txt(c, 'a fluent answer that is not supported by the facts', 910, 620, { size: 24, color: DIM, a: P(t, S.at(0) + 3.6, S.at(0) + 4.4) });
    c.restore();
  }
  // spot the error
  const ea = P(t, S.at(1) - .2, S.at(1) + .4) * (1 - .7 * P(t, S.at(3) - .3, S.at(3) + .4));
  if (ea > 0) {
    c.save(); c.globalAlpha = ea;
    const pz = S.pz(0);
    pill(c, 'SPOT THE ERROR', W / 2, 200, '#7ab8ff', { size: 20, align: 'center', solid: true });
    if (t > pz.s - .2 && t < pz.e + .4) { ring(c, W / 2 + 230, 200, 26, P(t, pz.s, pz.e), '#7ab8ff', 5, 1 - P(t, pz.e, pz.e + .4)); txt(c, String(Math.ceil(clamp(pz.e - t, 0, 9))), W / 2 + 230, 209, { size: 22, w: 700, f: F.mono, align: 'center', a: 1 - P(t, pz.e, pz.e + .4) }); }
    glass(c, 140, 280, 780, 420, { acc: '#7ab8ff' });
    txt(c, 'AI ASSISTANT', 180, 330, { size: 16, w: 700, f: F.mono, ls: 4, color: '#7ab8ff' });
    txt(c, 'Customer: Are you open on Sundays?', 180, 400, { size: 24, color: DIM });
    txt(c, 'Yes! We’re open Sundays', 180, 480, { size: 38, w: 600, f: F.head });
    txt(c, 'from 6 a.m. to 2 p.m.', 180, 535, { size: 38, w: 600, f: F.head });
    glass(c, 1000, 280, 780, 420, { acc: '#9aa6c2' });
    txt(c, 'SOURCE · HOURS.PDF', 1040, 330, { size: 16, w: 700, f: F.mono, ls: 4, color: '#9aa6c2' });
    [['Mon – Fri', '7:00 a.m. – 6:00 p.m.'], ['Saturday', '7:00 a.m. – 4:00 p.m.'], ['Sunday', '8:00 a.m. – 2:00 p.m.']].forEach(([d, h], i) => { txt(c, d, 1040, 420 + i * 70, { size: 28, w: 600 }); txt(c, h, 1740, 420 + i * 70, { size: 28, f: F.mono, align: 'right' }); });
    // scan + reveal
    const sc = P(t, S.at(2) - .2, S.at(2) + 1.6);
    if (sc > 0 && sc < 1) { const x = lerp(140, 1780, sc); c.save(); c.globalCompositeOperation = 'lighter'; const g = c.createLinearGradient(x - 80, 0, x + 20, 0); g.addColorStop(0, 'rgba(122,184,255,0)'); g.addColorStop(1, 'rgba(122,184,255,0.5)'); c.fillStyle = g; c.fillRect(x - 80, 270, 100, 440); c.restore(); }
    const rv = P(t, S.at(2) + 1.2, S.at(2) + 1.8);
    if (rv > 0) {
      const ex = 180 + measure(c, 'from ', { size: 38, w: 600, f: F.head }), ew = measure(c, '6 a.m.', { size: 38, w: 600, f: F.head });
      rr(c, ex - 8, 495, ew + 16, 54, 10); c.strokeStyle = hexA(BAD, rv); c.lineWidth = 3; c.stroke();
      rr(c, 1440, 545, 310, 50, 10); c.strokeStyle = hexA(GOOD, rv); c.stroke();
      glowLine(c, [[ex + ew + 10, 522], [lerp(ex + ew + 10, 1440, rv), lerp(522, 570, rv)]], BAD, rv, 2);
      pill(c, 'HALLUCINATION DETECTED', W / 2, 760, BAD, { size: 20, align: 'center', solid: true, a: P(t, S.at(2) + 1.8, S.at(2) + 2.2) });
    }
    c.restore();
  }
  // shield of safeguards
  const ga = P(t, S.at(3) - .3, S.at(3) + .4);
  if (ga > 0) {
    c.save(); c.fillStyle = `rgba(3,6,12,${.88 * ga})`; c.fillRect(0, 0, W, H); c.restore();
    const L = ['GROUNDING', 'CITATIONS', 'AUTOMATED EVALS', 'HUMAN REVIEW'];
    const cx = W / 2 + 160, cy = 470;
    L.forEach((s, i) => {
      const q = E.out(P(t, S.at(3) + i * 1.3, S.at(3) + i * 1.3 + .6)); const r = 120 + i * 62;
      c.save(); c.globalAlpha = ga * q; c.beginPath(); c.arc(cx, cy, r, Math.PI * 1.08, Math.PI * 1.92); c.strokeStyle = mix('#7ab8ff', '#3df5b0', i / 3); c.lineWidth = 16; c.lineCap = 'round'; c.stroke(); c.restore();
      const lc = mix('#7ab8ff', '#3df5b0', i / 3);
      c.save(); c.globalAlpha = ga * q; c.fillStyle = lc; c.beginPath(); c.arc(430, 250 + i * 70, 9, 0, 7); c.fill(); c.restore();
      txt(c, s, 456, 259 + i * 70, { size: 24, w: 700, f: F.mono, ls: 2, a: ga * q, color: lc });
    });
    glowDot(c, cx, cy - 20, 120, '#3df5b0', ga * .5); check(c, cx, cy - 40, 70, GOOD, P(t, S.at(3) + 5, S.at(3) + 5.6));
    const fa = P(t, S.at(3) + 5.2, S.at(3) + 6);
    glass(c, W / 2 - 300, 600, 920, 110, { acc: GOOD, a: fa, fill: .16 });
    txt(c, '“We’re open Sundays from 8 a.m. to 2 p.m.”', W / 2 - 260, 665, { size: 30, w: 600, f: F.head, a: fa });
    pill(c, '📎 Hours.pdf', W / 2 + 580, 655, GOOD, { size: 16, align: 'right', a: fa, f: F.mono });
    person(c, 'NOVA', 300, 1000, 1.05, { t, amp: S.amp('NOVA'), stage: 3, look: .7, a: P(t, S.at(4) - .5, S.at(4)) });
    kinetic(c, 'ENGINEERING = BUILD + TEST', W / 2 + 160, 830, P(t, S.at(4) + 1.6, S.at(4) + 2.8), { size: 40, w: 700, f: F.head, ls: 4, align: 'center', color: '#bcd6ff' });
  }
};

// ============================================================== CH8 — HORIZON
function icon(c, k, x, y, s, col, a) {
  c.save(); c.globalAlpha = a; c.translate(x, y); c.strokeStyle = col; c.fillStyle = col; c.lineWidth = 3;
  if (k === 0) for (let i = 0; i < 4; i++) { rr(c, -30 + i * 16, 20 - [30, 45, 20, 12][i], 11, [30, 45, 20, 12][i], 3); c.fill(); }
  if (k === 1) for (let i = 0; i < 3; i++) { rr(c, -34 + i * 24, -10, 20, 20, 5); c.stroke(); }
  if (k === 2) { c.beginPath(); c.ellipse(0, -18, 26, 8, 0, 0, 7); c.stroke(); c.beginPath(); c.moveTo(-26, -18); c.lineTo(-26, 20); c.ellipse(0, 20, 26, 8, 0, Math.PI, 0, true); c.lineTo(26, -18); c.stroke(); }
  if (k === 3) { rr(c, -22, -26, 44, 34, 10); c.stroke(); c.beginPath(); c.arc(-9, -9, 4, 0, 7); c.arc(9, -9, 4, 0, 7); c.fill(); rr(c, -16, 12, 32, 18, 6); c.stroke(); }
  if (k === 4) { c.beginPath(); c.moveTo(0, -30); c.quadraticCurveTo(26, -24, 26, -10); c.quadraticCurveTo(24, 16, 0, 30); c.quadraticCurveTo(-24, 16, -26, -10); c.quadraticCurveTo(-26, -24, 0, -30); c.stroke(); }
  c.restore();
}
SCENES.horizon = (c, S) => {
  const t = S.t;
  const pull = E.io(P(t, S.at(4) + 1.6, S.dur));
  // dawn
  const sunA = P(t, 0, 4);
  glowDot(c, W / 2, 900, 1100, '#ffb070', .28 * sunA); glowDot(c, W / 2, 900, 500, '#ffd27a', .3 * sunA);
  // network city appears on pull back
  if (pull > 0) {
    c.save(); c.globalCompositeOperation = 'lighter';
    for (let i = 0; i < 260; i++) { const x = hash(i) * W, y = 560 + hash(i + 1) * 520; const f = (y - 560) / 520; glowDot(c, x, y, 6 + f * 14, hash(i + 2) > .5 ? '#ffd27a' : '#4de8ff', pull * (.3 + f * .5)); }
    for (let i = 0; i < 80; i++) { const a = Math.floor(hash(i + 50) * 260), b = Math.floor(hash(i + 70) * 260); c.strokeStyle = hexA('#ffd27a', .12 * pull); c.beginPath(); c.moveTo(hash(a) * W, 560 + hash(a + 1) * 520); c.lineTo(hash(b) * W, 560 + hash(b + 1) * 520); c.stroke(); }
    c.restore();
  }
  c.save(); const sc = lerp(1, .45, pull); c.translate(W / 2, 1000); c.scale(sc, sc); c.translate(-W / 2, -1000);
  const st = t >= S.at(3) + 3.2 ? 4 : 3;
  person(c, 'NOVA', W / 2, 1000, 1.3, { t, amp: S.amp('NOVA'), stage: st });
  if (st === 4) glowDot(c, W / 2, 700, 400 * (1 + .1 * Math.sin(t * 2)), '#ffd27a', .25 * P(t, S.at(3) + 3.2, S.at(3) + 4));
  c.restore();
  // memory bubble
  const mb = P(t, S.at(0) + 1.5, S.at(0) + 2.2) * (1 - P(t, S.at(1) - .2, S.at(1) + .4));
  if (mb > 0) { glass(c, W / 2 - 260, 210, 520, 110, { acc: '#4de8ff', a: mb, r: 55 }); txt(c, '“How does this actually work?”', W / 2, 278, { size: 30, w: 600, f: F.head, align: 'center', a: mb }); }
  // memory cards (line 1/2)
  const ca = P(t, S.at(1), S.at(1) + .5) * (1 - P(t, S.at(3) - .3, S.at(3) + .3));
  if (ca > 0) {
    const lbl = ['PREDICTION', 'TOKENS', 'RETRIEVAL', 'AGENTS', 'TRUST'];
    const fr = [.08, .3, .5, .7, .85]; const d = S.end(1) - S.at(1);
    lbl.forEach((s, i) => {
      const on = P(t, S.at(1) + fr[i] * d, S.at(1) + fr[i] * d + .5);
      const x = W / 2 + (i - 2) * 300, y = 300 + Math.abs(i - 2) * 50 + Math.sin(t + i) * 6;
      glass(c, x - 120, y - 90, 240, 170, { acc: ACC[[1, 3, 4, 5, 7][i]], a: ca * (.3 + .7 * on), fill: .08 + on * .12 });
      icon(c, i, x, y - 25, 1, ACC[[1, 3, 4, 5, 7][i]], ca * (.4 + .6 * on));
      txt(c, s, x, y + 50, { size: 18, w: 700, f: F.mono, ls: 3, align: 'center', a: ca * (.4 + .6 * on) });
    });
  }
  // staircase (line 3)
  const sa = P(t, S.at(3) - .2, S.at(3) + .4) * (1 - P(t, S.at(4) - .3, S.at(4) + .3));
  if (sa > 0) {
    const fr = [.02, .1, .2, .32, .48]; const d = S.end(3) - S.at(3);
    TL.stages.forEach((s, i) => {
      const on = P(t, S.at(3) + fr[i] * d, S.at(3) + fr[i] * d + .4);
      const x = 180 + i * 330, y = 560 - i * 90;
      c.save(); c.globalAlpha = sa; rr(c, x, y, 300, 26, 8); c.fillStyle = hexA(STAGE_COL[i], .15 + .6 * on); c.fill(); c.restore();
      if (on > 0) glowDot(c, x + 150, y + 10, 160, STAGE_COL[i], .35 * on * sa);
      txt(c, s.toUpperCase(), x + 150, y - 20, { size: 24, w: 700, f: F.head, ls: 2, align: 'center', color: on > .5 ? STAGE_COL[i] : '#6b7590', a: sa });
    });
  }
  // final line
  const fa = P(t, S.at(4) - .1, S.at(4) + 1.2);
  if (fa > 0) {
    c.save(); c.fillStyle = `rgba(5,4,2,${.5 * fa})`; c.fillRect(0, 0, W, H); c.restore();
    const s = 'Your question is the first token.';
    kinetic(c, s, W / 2, 470, fa, { size: 82, w: 700, f: F.head, align: 'center', color: '#fff7e6' });
    const cw = measure(c, s, { size: 82, w: 700, f: F.head });
    if ((t * 1.6) % 1 < .55) { c.fillStyle = '#ffd27a'; c.fillRect(W / 2 + cw / 2 + 14, 400, 8, 84); }
  }
};

SCENES.end = (c, S) => {
  const t = S.t;
  kinetic(c, 'NEURAL HORIZON', W / 2, 360, P(t, .2, 1.6), { size: 96, w: 700, f: F.head, ls: 22, align: 'center', color: '#f2f7ff' });
  txt(c, 'A JOURNEY INTO ARTIFICIAL INTELLIGENCE', W / 2, 420, { size: 20, w: 600, f: F.mono, ls: 10, align: 'center', color: '#ffd27a', a: P(t, 1, 2) });
  const credits = [
    ['CAST', 'Nova · Arjun · Dr. Lin · Kai · Maya · Sam'],
    ['ANIMATION', 'Procedural motion graphics, rendered from code'],
    ['VOICES', 'Kokoro neural text-to-speech'],
    ['SCORE & SOUND', 'Original, synthesized for this film'],
    ['NOTE', 'Case-study figures, prices and token IDs are illustrative'],
  ];
  credits.forEach(([k, v], i) => {
    const a = P(t, 1.6 + i * .3, 2.2 + i * .3);
    txt(c, k, W / 2 - 30, 540 + i * 56, { size: 16, w: 700, f: F.mono, ls: 4, align: 'right', color: DIM, a });
    txt(c, v, W / 2 + 10, 540 + i * 56, { size: 24, w: 500, a });
  });
  for (let i = 0; i < 5; i++) { glowDot(c, W / 2 - 120 + i * 60, 900, 20, STAGE_COL[i], P(t, 3 + i * .15, 3.4 + i * .15)); c.fillStyle = STAGE_COL[i]; c.globalAlpha = P(t, 3 + i * .15, 3.4 + i * .15); c.beginPath(); c.arc(W / 2 - 120 + i * 60, 900, 6, 0, 7); c.fill(); c.globalAlpha = 1; }
};
