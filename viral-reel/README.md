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

---

# v3: 30 s cinematic Gen-Z edit

**File:** [`rohan_cinematic_30s.mp4`](rohan_cinematic_30s.mp4) (1080×1920, 30 s, original 100 BPM soundtrack with synced SFX)

- **Intro (0–6 s):** the letterbox opens like an eye, with dissolves, light leaks, typed "01.11.2026" / "a short film by rohan", the title *slow days*, and a waterfall in slow-mo with a riser and a beat-pause before the drop.
- **Drop 1 (6 s):** flash, RGB split, shake and a speed-ramp punch-in on the towers, then "rohan. (main character)".
- **Café run:** beat cuts at 0.6 / 1.2 s, whip pans with whoosh SFX, a speed-ramped waterfall, *coffee first.* and *no plans. no rush.*
- **Breakdown (17.4 s):** *breathe.* over slow-mo water with the real water sound.
- **Drop 2 (20.4 s):** faster city cuts and *golden hour hits different*.
- **Outro:** a slow pull-out on the sunset shot, *romanticize the ordinary.*, then the letterbox closes and "fin."

Look: teal/orange film grade, lifted blacks, halation glow, grain, vignette.

```bash
python3 make_music_cinematic.py cine.wav
python3 make_cinematic.py <assets_dir> cine_video.mp4     # ~12 min render
```
