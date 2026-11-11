#!/usr/bin/env bash
# Build the full documentary from the chapter scripts.
#   ./make_documentary.sh <work_dir> <out_dir>
# Needs: ffmpeg, python3 with pycairo numpy scipy soundfile kokoro-onnx,
#        fonts: EB Garamond + Inter, and the Kokoro model (see README.md).
set -euo pipefail
WORK=${1:?work dir}; OUT=${2:?output dir}
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$WORK" "$OUT"
cd "$HERE"
python3 parse_script.py
python3 tts.py "$WORK/kokoro-q8.onnx" "$WORK/voices.npz" "$WORK/tts_cache"
python3 build_timeline.py "$WORK/tts_cache" "$WORK/build"
for n in $(seq 1 10); do python3 music.py "$WORK/build" "$n"; done
# render chapters, two at a time
for n in $(seq 1 10); do
  f=$(printf "%s/chapter-%02d.mp4" "$OUT" "$n")
  python3 render.py "$WORK/build" "$n" "$f" &
  if (( n % 2 == 0 )); then wait; fi
done
wait
printf "file '%s'\n" "$OUT"/chapter-*.mp4 > "$WORK/concat.txt"
ffmpeg -y -loglevel error -f concat -safe 0 -i "$WORK/concat.txt" -c copy -movflags +faststart \
  "$OUT/if-claude-were-born-as-a-human-full.mp4"
echo "done: $OUT"
