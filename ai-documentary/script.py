"""Narration script + voice generation for NEURAL HORIZON.

Usage:  python3 script.py <kokoro_dir> <out_dir>

Synthesizes every line with Kokoro TTS (one voice per character), then lays
the lines out on a timeline and writes:
  out_dir/voice/*.wav      one file per line
  out_dir/timeline.json    scenes, line timings, lip-sync envelopes
  timeline.js              same data for the renderer (window.TIMELINE)
"""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

VOICES = {  # speaker -> (kokoro voice, speed, display name, role)
    "N": ("am_michael", 0.92, "Narrator", ""),
    "NOVA": ("af_heart", 1.0, "Nova", "the learner"),
    "ARJUN": ("bm_george", 0.98, "Arjun", "AI engineer"),
    "LIN": ("af_bella", 0.98, "Dr. Lin", "AI researcher"),
    "KAI": ("am_fenrir", 1.0, "Kai", "automation specialist"),
    "MAYA": ("bf_emma", 1.0, "Maya", "bakery owner"),
    "SAM": ("am_puck", 1.02, "Sam", "customer"),
}

CHAPTERS = [
    ("Prologue", ""),
    ("The Spark", "What an AI model really does"),
    ("Inside the Machine", "How a language model answers"),
    ("The Cost of Words", "Token optimization"),
    ("Memory & Truth", "Retrieval-augmented generation"),
    ("The Agents", "Models that plan, act and use tools"),
    ("The Problem Solver", "From business problem to product"),
    ("Trust", "Hallucinations, evaluation and guardrails"),
    ("The Horizon", "From beginner to expert"),
]
STAGES = ["Beginner", "AI User", "AI Builder", "AI Problem Solver", "AI Expert"]
CH_STAGE = [0, 0, 1, 1, 2, 2, 3, 3, 4]

P = "PAUSE"
SCENES = [
    dict(type="cold_open", ch=0, lines=[
        ("N", "In twenty twenty-six, you can talk to a machine that writes, reasons, and builds."),
        ("N", "But for most people, what happens inside is still a mystery."),
        ("N", "This is the story of one beginner who decided to find out."),
    ]),
    dict(type="title", ch=0, dur=6.5),
    # ---------------------------------------------------------------- 1
    dict(type="chapter", ch=1, dur=4.2),
    dict(type="nova_meets", ch=1, lines=[
        ("NOVA", "Okay. Everyone says AI is changing everything. I just don't get how it works."),
        ("N", "Meet Nova. Curious, a little skeptical, and starting from zero."),
        ("N", "Her first discovery: today's AI assistants are built on large language models, systems trained on enormous amounts of text to predict what comes next."),
        ("NOVA", "Wait. It's just predicting the next word?"),
        ("N", "Just prediction. But at a scale so large that grammar, facts, and patterns of reasoning emerge from it."),
    ]),
    # ---------------------------------------------------------------- 2
    dict(type="chapter", ch=2, dur=4.2),
    dict(type="llm_journey", ch=2, lines=[
        ("N", "Let's follow a single question on its journey through a model."),
        ("N", "First, the text is split into tokens: whole words, or pieces of words. And each token becomes a number."),
        ("N", "Each number is mapped to an embedding, a long list of values that places the token in a space of meaning."),
        ("N", "Now the vectors flow through dozens of transformer layers. In each one, attention lets every token look at the others, and decide what matters."),
        ("N", "At the end, the model scores every possible next token. It picks one, adds it to the text, and repeats, one token at a time, until the answer is complete."),
    ]),
    dict(type="quiz", ch=2, lines=[
        ("N", "Quick check. Does a language model look the answer up in a database before it replies?"),
        (P, 3.2),
        ("N", "Not by default. A plain language model answers from patterns stored in its weights during training. Which is exactly why the next chapters matter.", {"impact": True}),
    ]),
    # ---------------------------------------------------------------- 3
    dict(type="chapter", ch=3, dur=4.2),
    dict(type="token_compare", ch=3, lines=[
        ("ARJUN", "Every token you send costs money and time. Let me show you something."),
        ("N", "Two workflows. Same task: summarize a customer's complaint, and draft a reply."),
        ("N", "On the left, the entire forty-page policy manual and the full chat history are pasted into every request."),
        ("N", "On the right, only the relevant policy section, and a short summary of the conversation."),
        ("N", "Same quality answer. About ninety percent fewer input tokens. Lower cost, and a faster response.", {"impact": True}),
        ("NOVA", "So better context beats more context."),
    ]),
    # ---------------------------------------------------------------- 4
    dict(type="chapter", ch=4, dur=4.2),
    dict(type="rag", ch=4, lines=[
        ("LIN", "A model's knowledge is frozen when training ends. It has never seen your company's documents."),
        ("N", "Retrieval-augmented generation fixes that. Documents are split into chunks. Each chunk becomes an embedding, stored in a vector database."),
        ("N", "When a question arrives, it is embedded too, and the system searches for the chunks closest in meaning."),
        ("N", "The best matches are placed into the prompt, right alongside the question."),
        ("N", "Now the model answers from real sources, and can cite them.", {"impact": True}),
        ("NOVA", "So the model doesn't change. It just gets the right pages at the right moment."),
        ("LIN", "Exactly. No retraining required."),
    ]),
    # ---------------------------------------------------------------- 5
    dict(type="chapter", ch=5, dur=4.2),
    dict(type="agents", ch=5, lines=[
        ("KAI", "A chatbot answers. An agent acts."),
        ("N", "An agent is a model running in a loop. It plans a step, calls a tool, observes the result, and decides what to do next."),
        ("N", "Bigger jobs can be split across several agents. A planner breaks down the goal. A researcher gathers data. A builder creates the output. A reviewer checks it."),
        ("N", "They pass results to each other, use tools like databases, code, and email, and hand back a finished task."),
        ("KAI", "The trick is giving each agent clear instructions, the right tools, and firm limits on what it's allowed to do."),
    ]),
    dict(type="challenge", ch=5, lines=[
        ("N", "Challenge. Which of these actions should an agent be allowed to take on its own?"),
        (P, 3.4),
        ("N", "Low-risk, reversible actions can be automated. Anything costly or irreversible should wait for a human to approve it.", {"impact": True}),
    ]),
    # ---------------------------------------------------------------- 6
    dict(type="chapter", ch=6, dur=4.2),
    dict(type="problem", ch=6, lines=[
        ("MAYA", "We get two hundred messages a day. Same questions. Opening hours, allergens, order status. We miss half of them."),
        ("SAM", "I asked if the cake was nut-free. Nobody replied, so I ordered somewhere else."),
        ("N", "Nova sees it. This isn't a technology problem. It's a business problem: lost orders, and an overwhelmed team."),
        ("N", "She designs the solution. An assistant grounded in the bakery's menu and policies, connected to the order system, with a handoff to staff for anything unusual."),
    ]),
    dict(type="ship", ch=6, lines=[
        ("N", "Before launch, she tests it against one hundred real customer questions, and fixes every wrong answer she finds."),
        ("N", "Then, she ships it.", {"impact": True}),
        ("MAYA", "Replies went from hours to seconds. And my team finally has time to bake."),
        ("N", "Start with a real problem. Ground the AI in real data. Test it. And keep a human in the loop."),
    ]),
    # ---------------------------------------------------------------- 7
    dict(type="chapter", ch=7, dur=4.2),
    dict(type="trust", ch=7, lines=[
        ("LIN", "Language models can sound completely confident, and still be wrong. We call that a hallucination."),
        ("N", "Spot the error."),
        (P, 2.6),
        ("N", "The assistant says the bakery opens at six on Sundays. The source document says eight.", {"impact": True}),
        ("N", "Grounding, citations, automated evaluations, and human review catch mistakes like this, before customers do."),
        ("NOVA", "So building with AI isn't just prompting. It's engineering, with testing."),
    ]),
    # ---------------------------------------------------------------- 8
    dict(type="chapter", ch=8, dur=4.2),
    dict(type="horizon", ch=8, lines=[
        ("N", "Nova started with one question. How does this actually work?"),
        ("N", "She learned how models predict. How to spend tokens wisely. How to ground answers in real knowledge. How agents act. And how to turn all of it into something people trust."),
        ("NOVA", "The tools will keep changing. The real skill is knowing which problem is worth solving."),
        ("N", "Beginner. User. Builder. Problem solver. Expert. The path is open to anyone willing to start."),
        ("N", "Your question is the first token.", {"impact": True}),
    ], tail=2.2),
    dict(type="end", ch=8, dur=8.0),
]

LEAD, TAIL, GAP, GAP_SPK = 0.9, 1.1, 0.42, 0.6
SR = 24000
FPS = 30


def main():
    kdir, out = Path(sys.argv[1]), Path(sys.argv[2])
    (out / "voice").mkdir(parents=True, exist_ok=True)
    k = Kokoro(str(kdir / "kokoro-v1.0.onnx"), str(kdir / "voices-v1.0.bin"))
    t = 0.0
    scenes, n = [], 0
    for si, sc in enumerate(SCENES):
        start = t
        lines, pauses = [], []
        if "lines" in sc:
            lt = LEAD
            prev = None
            for item in sc["lines"]:
                if item[0] == P:
                    pauses.append(dict(s=round(lt, 3), e=round(lt + item[1], 3)))
                    lt += item[1] + GAP
                    continue
                who, text = item[0], item[1]
                opts = item[2] if len(item) > 2 else {}
                if prev is not None and prev != who:
                    lt += GAP_SPK - GAP
                voice, speed, *_ = VOICES[who]
                wav = out / "voice" / f"{n:03d}_{who}.wav"
                if not wav.exists():
                    s, sr = k.create(text, voice=voice, speed=speed, lang="en-gb" if voice[0] == "b" else "en-us")
                    s = trim(s, sr)
                    sf.write(wav, s, sr)
                s, sr = sf.read(wav)
                d = len(s) / sr
                lines.append(dict(who=who, text=text, s=round(lt, 3), e=round(lt + d, 3),
                                  wav=wav.name, env=envelope(s, sr), impact=bool(opts.get("impact"))))
                print(f"{n:03d} {who:5s} {d:5.2f}s  {text[:60]}")
                n += 1
                lt += d + GAP
                prev = who
            dur = lt - GAP + sc.get("tail", TAIL)
        else:
            dur = sc["dur"]
        scenes.append(dict(i=si, type=sc["type"], ch=sc["ch"], start=round(start, 3), dur=round(dur, 3),
                           lines=lines, pauses=pauses))
        t += dur
    data = dict(fps=FPS, duration=round(t, 3), chapters=CHAPTERS, stages=STAGES, ch_stage=CH_STAGE,
                speakers={k_: dict(name=v[2], role=v[3]) for k_, v in VOICES.items()}, scenes=scenes)
    (out / "timeline.json").write_text(json.dumps(data))
    Path(__file__).with_name("timeline.js").write_text("window.TIMELINE=" + json.dumps(data) + ";\n")
    print(f"total {t:.1f}s  ({t/60:.2f} min), {n} lines")


def trim(s, sr, thr=0.01):
    idx = np.where(np.abs(s) > thr)[0]
    if len(idx) == 0:
        return s
    a = max(0, idx[0] - int(0.03 * sr))
    b = min(len(s), idx[-1] + int(0.08 * sr))
    return s[a:b]


def envelope(s, sr):
    hop = sr // FPS
    m = len(s) // hop
    r = np.sqrt(np.mean(s[: m * hop].reshape(m, hop) ** 2, axis=1))
    r = r / (np.percentile(r, 95) + 1e-9)
    return [round(float(min(1, v)), 2) for v in r]


if __name__ == "__main__":
    main()
