"""Shared timeline for the 30 s cinematic edit (used by video + music scripts).

100 BPM -> 1 beat = 0.6 s.  Sections:
  0.0 - 6.0   intro      letterbox opens, dissolves, slow-mo, riser
  6.0         DROP 1     flash + RGB split + shake
  6.0 - 17.4  cafe/city  beat cuts (0.6 / 1.2 s), whip pans, speed ramps
  17.4 - 20.4 breakdown  "breathe." slow-mo waterfall
  20.4        DROP 2
  20.4 - 26.4 city       faster cuts
  26.4 - 30.0 outro      slow pull-out, letterbox closes
"""
BPM = 100
BEAT = 60 / BPM
DUR = 30.0
DROPS = [6.0, 20.4]
BREAK = (17.4, 20.4)
OUTRO = 26.4

# (start, end, source, motion, transition_in)
#   source: photo key, ("crop", key, box) or ("vid", src_start, mode)
#   motion: dict(z=(from,to), c=((x0,y0),(x1,y1))) centre in 0..1 of free space
#   transition_in: "cut" | "dissolve" | "whipL" | "whipR" | "hit"
SHOTS = [
    (0.0, 2.4, ("crop", "lake", (0.30, 0.0, 0.75, 1.0)), dict(z=(1.10, 1.10), c=((0.0, 0.5), (1.0, 0.5))), "cut"),
    (2.4, 4.2, ("crop", "towers", (0.40, 0.0, 0.94, 0.54)), dict(z=(1.12, 1.05), c=((0.5, 1.0), (0.5, 0.0))), "dissolve"),
    (4.2, 6.0, ("vid", 0.2, "slow"), dict(z=(1.04, 1.12)), "dissolve"),
    (6.0, 7.2, "look_up", dict(z=(1.30, 1.04), c=((0.5, 0.4), (0.5, 0.5)), ramp=True), "hit"),
    (7.2, 8.4, "towers", dict(z=(1.03, 1.10), c=((0.5, 0.6), (0.5, 0.5))), "whipL"),
    (8.4, 9.0, "coffee", dict(z=(1.12, 1.18), c=((0.4, 0.5), (0.5, 0.5))), "cut"),
    (9.0, 10.2, "cafe_smile", dict(z=(1.06, 1.14), c=((0.5, 0.5), (0.5, 0.5))), "whipR"),
    (10.2, 10.8, "food", dict(z=(1.0, 1.08)), "cut"),
    (10.8, 12.0, "cafe_look", dict(z=(1.14, 1.06), c=((0.4, 0.5), (0.6, 0.5))), "whipL"),
    (12.0, 13.2, ("vid", 1.8, "ramp"), dict(z=(1.15, 1.04)), "hit"),
    (13.2, 13.8, ("crop", "cafe_hands", (0.2, 0.28, 0.95, 0.9)), dict(z=(1.04, 1.12)), "cut"),
    (13.8, 15.0, ("crop", "cafe_side", (0.25, 0.22, 0.95, 0.92)), dict(z=(1.10, 1.03)), "whipR"),
    (15.0, 16.2, ("crop", "lake", (0.0, 0.0, 0.32, 1.0)), dict(z=(1.06, 1.06), c=((0.2, 0.5), (0.8, 0.5))), "whipL"),
    (16.2, 17.4, ("crop", "lake", (0.40, 0.45, 0.62, 1.0)), dict(z=(1.04, 1.12)), "cut"),
    (17.4, 20.4, ("vid", 3.0, "slow"), dict(z=(1.0, 1.10)), "dissolve"),
    (20.4, 21.6, ("crop", "look_up", (0.37, 0.0, 0.98, 0.61)), dict(z=(1.30, 1.04), ramp=True), "hit"),
    (21.6, 22.2, ("crop", "lake", (0.68, 0.0, 1.0, 1.0)), dict(z=(1.06, 1.12)), "cut"),
    (22.2, 22.8, ("vid", 5.0, "real"), dict(z=(1.06, 1.10)), "cut"),
    (22.8, 24.0, ("crop", "sky_back", (0.1, 0.25, 0.9, 1.0)), dict(z=(1.12, 1.04)), "whipR"),
    (24.0, 25.2, ("vid", 6.2, "ramp"), dict(z=(1.12, 1.04)), "hit"),
    (25.2, 26.4, ("crop", "towers", (0.12, 0.50, 0.66, 0.985)), dict(z=(1.04, 1.12)), "whipL"),
    (26.4, 30.0, "sky_back", dict(z=(1.18, 1.0), c=((0.5, 0.6), (0.5, 0.5))), "dissolve"),
]

WHIPS = [s[0] for s in SHOTS if s[4].startswith("whip")]
HITS = [s[0] for s in SHOTS if s[4] == "hit"]
DISSOLVES = [s[0] for s in SHOTS if s[4] == "dissolve"]
CUTS = [s[0] for s in SHOTS if s[4] == "cut" and s[0] > 0]
