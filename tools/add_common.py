# -*- coding: utf-8 -*-
"""Append Ren'Py's engine strings (tl/korean/common.rpy) to the unit list.

merge_tl.py only carried the game's own strings, so engine messages such as
"Loading will lose unsaved progress." stayed English.  New units are appended
after the existing ones so already-translated indices (i) do not move.
Writes work/chunks/chunk_045.json (with the official Japanese for reference).
"""
import os, sys, json, shutil, tempfile

sys.stdout.reconfigure(encoding="utf-8")
W = os.environ.get("TS_WORKSPACE") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(W, "tools"))
import units as U

SRC = os.path.join(W, "proj_src", "game", "tl", "korean", "common.rpy")
DST = os.path.join(W, "tl_korean", "common.rpy")
UNITS = os.path.join(W, "work", "units.json")
JA = os.path.join(W, "decompiled", "tl", "japanese", "common.rpy")


def ja_strings():
    out, old = {}, None
    for raw in open(JA, encoding="utf-8-sig"):
        s = raw.strip()
        if s.startswith("old "):
            q = U.split_quoted(raw)
            old = q[1] if q else None
        elif s.startswith("new ") and old is not None:
            q = U.split_quoted(raw)
            out[old] = q[1] if q else ""
            old = None
    return out


def main():
    us = json.load(open(UNITS, encoding="utf-8"))
    if any(u["file"] == "common.rpy" for u in us):
        sys.exit("common.rpy units already present")
    shutil.copy(SRC, DST)
    tmp = tempfile.mkdtemp()
    shutil.copy(SRC, os.path.join(tmp, "common.rpy"))
    new = U.extract(tmp)
    ja = ja_strings()
    base = len(us)
    for u in new:
        if ja.get(u["src"]):
            u["ja"] = ja[u["src"]]
    us.extend(new)
    json.dump(us, open(UNITS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    chunk = [dict({"i": base + k, "who": "", "src": u["src"]}, **({"ja": u["ja"]} if u.get("ja") else {}))
             for k, u in enumerate(new) if U.needs_translation(u)]
    json.dump(chunk, open(os.path.join(W, "work", "chunks", "chunk_045.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"appended {len(new)} units (i {base}..{base + len(new) - 1}), "
          f"chunk_045: {len(chunk)} rows, with ja: {sum(1 for c in chunk if 'ja' in c)}")


if __name__ == "__main__":
    main()
