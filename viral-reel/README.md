# "Slow Day in the City": Instagram reel

**Final video:** [`rohan_city_reel.mp4`](rohan_city_reel.mp4) (1080×1920, 30 fps, 21 s, H.264/AAC, -14 LUFS)

## The edit (beat-synced to a 120 BPM original track)
| Time | Shot | On-screen text |
|---|---|---|
| 0–2 s | Looking up at the twin towers (hook, push-in) | POV: you stopped / **waiting for the weekend** |
| 2 s | **DROP**: flash, shake, waterfall in 0.5× slow-mo | *find your quiet place* |
| 4–10 s | Café sequence, one cut per 2 beats with zoom punches | coffee. / views. / deep thoughts. / table 17. / good food. / no rush. |
| 10–12 s | Breakdown: waterfall slow-mo with real water sound | *breathe in.* |
| 12 s | **Second drop**: lake panorama pan | this city has / *its moments* |
| 15–17 s | Standing under the towers (pull-out) | *and so do you* |
| 17–21 s | Back view to the sunset sky | *romanticize* / **your own life** + "save this" CTA |

Look: warm-highlight / teal-shadow golden-hour grade, soft S-curve, light film grain, vignette.
Captions stay inside the IG safe zone (clear of the bottom UI and right-side buttons).
The music is synthesized from scratch in `make_music.py`, so there are no copyright strikes.

## Posting tips
- **Caption:** `not every day needs a plan ☕🌇 just good coffee, a quiet corner and this skyline. save this for your next slow day 🤍`
- **Hashtags:** `#slowliving #cityvibes #romanticizeyourlife #cafevibes #aestheticreels #goldenhour #mumbaidiaries #weekendvibes #reelsindia #explorepage`
- Swapping in a trending audio is optional: the cuts land every 0.5 s / 1 s, so any ~120 BPM track lines up. Keep the original audio at ~20% so the water sound stays in.
- Post at 7–9 pm local time. Put the hook text in the cover frame (frame at 0.5 s).

## Re-render
```bash
python3 make_music.py music.wav
python3 make_reel.py <folder with the photos + clip> music.wav rohan_city_reel.mp4
```
Needs Python 3 with numpy and Pillow, plus ffmpeg.

---

# v2: matches the reference reel's style

**Files:** [`rohan_reel_v2.mp4`](rohan_reel_v2.mp4) (with an original lo-fi track) and
[`rohan_reel_v2_no_music.mp4`](rohan_reel_v2_no_music.mp4) (silent, for adding a trending sound inside Instagram)

What it copies from the reference: 21 shots with a hard cut **exactly every 0.8 s** (scene detection gives the same cut
times as the reference: 0.8, 1.6 … 16.0 s), no transitions, a slow handheld drift on every shot, a warm sunset grade,
and a bold-italic yellow location title with 😍 on the first 4 shots. Length is 17.1 s, the same as the reference.

**To use the reference reel's song:** upload `rohan_reel_v2_no_music.mp4`, tap *Add audio*, pick the same sound,
and start it at the beat. The cuts follow its 0.8 s rhythm (75 BPM).

```bash
python3 make_music_lofi.py lofi.wav 17.1
python3 make_reel_v2.py <assets_dir> v2_video.mp4 "Lakeside Café"   # title text is the 3rd argument
ffmpeg -i v2_video.mp4 -i lofi.wav -map 0:v -map 1:a -c:v copy -af loudnorm=I=-14:TP=-1 -c:a aac -b:a 192k rohan_reel_v2.mp4
```
