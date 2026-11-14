# NEURAL HORIZON — an animated AI documentary

`neural_horizon.mp4`: 7 min 10 s, 1920×1080, 30 fps, AAC stereo at −16 LUFS.

Nova is a beginner who works through eight chapters and goes from **Beginner → AI User → AI Builder → AI Problem Solver → AI Expert**.

| # | Chapter | Concept shown on screen |
|---|---------|-----------------------------|
| 1 | The Spark | Next-token prediction demo |
| 2 | Inside the Machine | Question → tokens/IDs → embeddings → transformer layers + attention → next-token scores → repeat; **knowledge check** |
| 3 | The Cost of Words | Side-by-side workflows: 18,400 vs 1,650 input tokens (−91%); techniques |
| 4 | Memory & Truth | RAG: chunk → embed/store → similarity search → augment prompt → cited answer |
| 5 | The Agents | Plan/act/observe loop, 4 cooperating agents with tools; **permissions challenge** |
| 6 | The Problem Solver | Bakery case study: problem → blueprint → 100-question eval → ship → before/after |
| 7 | Trust | **Spot-the-error** hallucination, safeguards (grounding, citations, evals, human review) |
| 8 | The Horizon | Recap and progression |

Cast: Nova (learner), Arjun (AI engineer), Dr. Lin (researcher), Kai (automation specialist), Maya (business owner), Sam (customer). Each has a separate voice and lip-sync driven by the audio.

## Rebuild

```bash
pip install kokoro-onnx soundfile numpy        # + kokoro-v1.0.onnx / voices-v1.0.bin from the kokoro-onnx GitHub release
python3 script.py <kokoro_dir> build           # voices + timeline.json / timeline.js
node render.mjs build/video.mp4 4              # Playwright renders doc.html frame by frame → 4 parts
ffmpeg -f concat -safe 0 -i build/video.mp4.txt -c copy build/video.mp4
python3 audio.py build                         # score, SFX, narration mix with ducking → build/mix.wav
ffmpeg -i build/video.mp4 -i build/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k \
       -af loudnorm=I=-16:TP=-1.5 -shortest -movflags +faststart neural_horizon.mp4
```

Open `doc.html` in a browser to preview (`?t=120` jumps to a time).

Files: `script.py` (narration + timeline), `engine.js` (characters, glass UI, HUD, subtitles, 7 transition types), `scenes.js` (one renderer per scene), `audio.py` (score/SFX/mix).

The case-study figures, prices, token IDs and probabilities are illustrative, and the video labels them that way.
