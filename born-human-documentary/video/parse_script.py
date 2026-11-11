"""Parse the chapter markdown files into a timeline-ready script.json.

Each scene becomes a list of items in document order:
  {"type": "line", "voice": <speaker>, "text": ...}   narration or dialogue
  {"type": "pause", "sec": ...}                       (beat) markers
plus on-screen titles and quotes for the renderer.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHAP = sorted((ROOT / "chapters").glob("*.md"))

SCENE_RE = re.compile(r"^### Scene (\d+)\.(\d+) — (.+?) \((\d+):(\d+)–(\d+):(\d+)\)")
DIALOGUE_RE = re.compile(r"^> \*\*([A-Z][A-Z .']+?)(?: \([^)]*\))?:\*\*\s*(.*)$")
SKIP_NARR = ("*Note", "*Tone note", "*Production note", "*(No narration", "*(None", "*(Silence")


def clean_spoken(t):
    t = re.sub(r"\*\*\([^)]*\)\*\*", "", t)          # **(Step 1)** / **(①)**
    t = re.sub(r"\*\([^*]*\)\*", "", t)              # *(stage direction)*
    t = re.sub(r"\([^)]*\)", "", t) if t.strip().startswith("(") else t
    t = t.replace("*", "").replace("“", '"').replace("”", '"')
    t = re.sub(r"₹\s?([\d,\.]+)\s*(lakh|crore)?", lambda m: f"{m.group(1)} {m.group(2) + ' ' if m.group(2) else ''}rupees", t)
    t = t.replace(" — ", ", ").replace("—", ", ")
    t = re.sub(r"\s+", " ", t).strip()
    t = t.strip('"').strip()
    t = t.replace('" "', " ")
    return t


def strip_md(t):
    return re.sub(r"\s+", " ", t.replace("*", "").strip())


def parse_chapter(path):
    lines = path.read_text().splitlines()
    title = lines[0].lstrip("# ").strip()
    num = int(path.name[:2])
    scenes, sc, mode = [], None, None
    quote_buf = None
    for raw in lines:
        m = SCENE_RE.match(raw)
        if m:
            sc = {"id": f"{m.group(1)}.{m.group(2)}", "title": m.group(3), "items": [],
                  "titles": [], "quotes": [], "visual": "",
                  "tc": [int(m.group(4)) * 60 + int(m.group(5)), int(m.group(6)) * 60 + int(m.group(7))]}
            scenes.append(sc)
            mode = "visual"
            continue
        if sc is None:
            continue
        if raw.startswith("## "):          # end of storyboard
            sc = None
            continue
        if raw.startswith("**Visual:**"):
            sc["visual"] = strip_md(raw[len("**Visual:**"):])[:400]
        if raw.startswith("**NARRATION"):
            mode = "narr"
            continue
        if raw.startswith("**On-screen quote") or raw.startswith("**On-screen text"):
            mode = "quote"
            quote_buf = {"text": [], "attr": ""}
            sc["quotes"].append(quote_buf)
            continue
        if raw.startswith("**On-screen title"):
            parts = re.findall(r"\*([^*]+)\*", raw.split(":**", 1)[1])
            sc["titles"].extend(p.strip() for p in parts if p.strip())
            continue
        if raw.startswith("**") and not raw.startswith("**NARRATION"):
            if mode == "quote":
                mode = "visual"
            if mode == "narr" and not raw.startswith("**("):
                mode = "visual"
        if raw.startswith("→") or raw.startswith("---"):
            mode = "visual"
            continue
        if not raw.startswith(">"):
            continue
        body = raw[1:].strip()
        if not body:
            continue
        if mode == "quote":
            if body.startswith("—"):
                quote_buf["attr"] = strip_md(body.lstrip("— "))
            else:
                quote_buf["text"].append(strip_md(body).strip('"'))
            continue
        dm = DIALOGUE_RE.match(raw)
        if dm:
            speaker = dm.group(1).strip()
            text = clean_spoken(dm.group(2))
            if text:
                sc["items"].append({"type": "line", "voice": speaker, "text": text,
                                    "display": f"{speaker.title()}: {text}"})
            continue
        if mode == "narr":
            if body.startswith(SKIP_NARR):
                if body.startswith("*(No narration") or body.startswith("*(None") or body.startswith("*(Silence"):
                    sc["items"].append({"type": "pause", "sec": 5.0})
                continue
            beats = re.findall(r"\*\((long beat|beat)[^)]*\)\*", body)
            text = clean_spoken(body)
            if text:
                sc["items"].append({"type": "line", "voice": "NARRATOR", "text": text, "display": text})
            for b in beats:
                sc["items"].append({"type": "pause", "sec": 2.2 if b == "long beat" else 1.2})
    return {"num": num, "title": title, "scenes": scenes}


if __name__ == "__main__":
    data = [parse_chapter(p) for p in CHAP]
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "script.json"
    out.write_text(json.dumps(data, indent=1, ensure_ascii=False))
    words = 0
    for ch in data:
        w = sum(len(i["text"].split()) for s in ch["scenes"] for i in s["items"] if i["type"] == "line")
        words += w
        print(ch["num"], ch["title"][:40], len(ch["scenes"]), "scenes", w, "words")
    print("total words", words)
