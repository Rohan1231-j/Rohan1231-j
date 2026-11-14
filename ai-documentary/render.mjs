// Render frames with headless Chromium and pipe them to ffmpeg.
// node render.mjs <out.mp4> [workers] [start end]   (also: --stills t1,t2,... <dir>)
import { createRequire } from 'node:module';
const req = createRequire(import.meta.url);
let pw; try { pw = req('playwright'); } catch { pw = req(process.env.PLAYWRIGHT_PATH || '/opt/node-tools/node_modules/playwright'); }
const { chromium } = pw;
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import fs from 'node:fs';
const here = path.dirname(fileURLToPath(import.meta.url));
const url = 'file://' + path.join(here, 'doc.html') + '?render';
const args = process.argv.slice(2);

async function page(browser) {
  const p = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  p.on('pageerror', e => console.error('PAGEERR', e.message));
  await p.goto(url); await p.evaluate(() => window.ready);
  return p;
}
const grab = (p, t) => p.evaluate(t => { renderAt(t); return document.getElementById('c').toDataURL('image/jpeg', 0.94).split(',')[1]; }, t);

const browser = await chromium.launch({ args: ['--disable-gpu-vsync', '--force-color-profile=srgb'] });
if (args[0] === '--stills') {
  const ts = args[1].split(',').map(Number); const dir = args[2]; fs.mkdirSync(dir, { recursive: true });
  const p = await page(browser);
  for (const t of ts) fs.writeFileSync(path.join(dir, `f_${t.toFixed(1).padStart(6, '0')}.jpg`), Buffer.from(await grab(p, t), 'base64'));
  await browser.close(); process.exit(0);
}
const out = args[0]; const workers = +(args[1] || 4);
const TL = JSON.parse(fs.readFileSync(path.join(here, 'timeline.js'), 'utf8').replace(/^window.TIMELINE=/, '').replace(/;\s*$/, ''));
const fps = TL.fps; const t0 = +(args[2] || 0), t1 = +(args[3] || TL.duration);
const N = Math.round((t1 - t0) * fps); const per = Math.ceil(N / workers);
const parts = [];
const started = Date.now();
await Promise.all(Array.from({ length: workers }, async (_, w) => {
  const a = w * per, b = Math.min(N, a + per); if (a >= b) return;
  const part = out.replace(/\.mp4$/, `.part${w}.mp4`); parts[w] = part;
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', '-tune', 'animation', part], { stdio: ['pipe', 'inherit', 'inherit'] });
  const p = await page(browser);
  for (let f = a; f < b; f++) {
    const buf = Buffer.from(await grab(p, t0 + f / fps), 'base64');
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (w === 0 && f % 150 === 0) console.log(`w0 ${f - a}/${b - a}  ${((Date.now() - started) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
}));
await browser.close();
fs.writeFileSync(out + '.txt', parts.filter(Boolean).map(p => `file '${p}'`).join('\n'));
console.log('done', ((Date.now() - started) / 1000).toFixed(0) + 's');
