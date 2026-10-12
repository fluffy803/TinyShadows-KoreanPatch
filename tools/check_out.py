# -*- coding: utf-8 -*-
"""Pre-build checks on translated chunks: Ren'Py-breaking characters and font coverage."""
import os, sys, json, glob

sys.stdout.reconfigure(encoding="utf-8")
from fontTools.ttLib import TTFont

W = os.environ.get("TS_WORKSPACE") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
units = json.load(open(os.path.join(W, "work", "units.json"), encoding="utf-8"))
fonts = {f: set(TTFont(os.path.join(W, "extracted", f)).getBestCmap())
         for f in ("ChillRoundGothic_Medium.ttf", "ChillRoundGothic_Bold.ttf")}

SPECIAL = ["[", "]", "{", "}", '"', "\\"]
bad, chars = [], set()
for p in sorted(glob.glob(os.path.join(W, "work", "chunks", "*.out.json"))):
    lyrics = p.endswith("lyrics.out.json")
    for r in json.load(open(p, encoding="utf-8")):
        d = r["dst"]
        chars |= set(d)
        if "\n" in d or "\r" in d:
            bad.append((os.path.basename(p), r["i"], "raw newline (use \\\\n)", d[:70]))
        if lyrics:
            continue
        src = units[r["i"]]["src"]
        for ch in SPECIAL:
            if ch in d and ch not in src:
                bad.append((os.path.basename(p), r["i"], ch, d[:70]))

print("special-char issues:", len(bad))
for b in bad:
    print("  ", b)
for f, cmap in fonts.items():
    miss = sorted(c for c in chars if ord(c) > 127 and ord(c) not in cmap)
    print(f"missing in {f}: {len(miss)} {''.join(miss)}")
