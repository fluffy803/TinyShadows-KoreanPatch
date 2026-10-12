# -*- coding: utf-8 -*-
"""Extract / re-apply translatable text in a Ren'Py tl/<lang> tree.

Structure is never handed to the translator: only the quoted payloads are
extracted, and they are written back into the exact same slots.

  extract:  python units.py extract <tl_dir> <units.json>
  apply:    python units.py apply <tl_dir> <units.json> <out_tl_dir>
  chunk:    python units.py chunk <units.json> <outdir> <units_per_chunk>
  collect:  python units.py collect <units.json> <chunkdir> <out_units.json>
"""
import os, sys, json, re, shutil

TRANSLATE_HDR = re.compile(r"^translate\s+\w+\s+([\w.]+):\s*$")
STRINGS_HDR = re.compile(r"^translate\s+\w+\s+strings:\s*$")


def split_quoted(line):
    """Return (prefix, inner, suffix) for the first double-quoted string, or None."""
    i = line.find('"')
    if i < 0:
        return None
    j = i + 1
    while j < len(line):
        c = line[j]
        if c == "\\":
            j += 2
            continue
        if c == '"':
            return line[:i + 1], line[i + 1:j], line[j:]
        j += 1
    return None


def extract(tl_dir):
    units = []
    for root, _, files in os.walk(tl_dir):
        for fn in sorted(files):
            if not fn.endswith(".rpy"):
                continue
            path = os.path.join(root, fn)
            rel = os.path.relpath(path, tl_dir).replace("\\", "/")
            lines = open(path, encoding="utf-8-sig").read().split("\n")

            in_block = None      # current translate <id> block
            in_strings = False
            seen_body = 0        # how many payload lines seen in this block
            n_comment = 0        # how many commented-out originals precede
            pending_old = None

            for ln, raw in enumerate(lines):
                s = raw.strip()

                m = TRANSLATE_HDR.match(raw)
                if STRINGS_HDR.match(raw):
                    in_strings, in_block = True, None
                    continue
                if m:
                    in_strings = False
                    in_block = m.group(1)
                    seen_body = 0
                    n_comment = 0
                    continue

                if in_strings:
                    if s.startswith("old "):
                        q = split_quoted(raw)
                        pending_old = q[1] if q else None
                    elif s.startswith("new ") and pending_old is not None:
                        q = split_quoted(raw)
                        if q:
                            units.append({
                                "file": rel, "line": ln, "kind": "string",
                                "id": pending_old, "who": "", "src": pending_old,
                                "dst": "",
                            })
                        pending_old = None
                    continue

                if in_block:
                    if not s:
                        continue
                    if s.startswith("#"):
                        n_comment += 1
                        continue
                    q = split_quoted(raw)
                    if not q:
                        continue
                    pre, inner, _ = q
                    who = pre.strip().rstrip('"').strip()
                    units.append({
                        "file": rel, "line": ln, "kind": "dialogue",
                        "id": in_block, "who": who, "src": inner, "dst": "",
                        "slot": seen_body,
                    })
                    seen_body += 1
    return units


def apply(tl_dir, units, out_dir):
    by_file = {}
    for u in units:
        by_file.setdefault(u["file"], []).append(u)

    if os.path.abspath(tl_dir) != os.path.abspath(out_dir):
        if os.path.exists(out_dir):
            shutil.rmtree(out_dir)
        shutil.copytree(tl_dir, out_dir)

    changed = skipped = 0
    for rel, us in by_file.items():
        path = os.path.join(out_dir, rel.replace("/", os.sep))
        text = open(path, encoding="utf-8-sig").read()
        lines = text.split("\n")
        for u in us:
            dst = u.get("dst") or ""
            if not dst:
                skipped += 1
                continue
            ln = u["line"]
            q = split_quoted(lines[ln])
            if not q:
                skipped += 1
                continue
            pre, inner, suf = q
            if inner != u["src"]:
                skipped += 1
                continue
            lines[ln] = pre + dst + suf
            changed += 1
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    print(f"applied {changed} lines, skipped {skipped}")


CJK = re.compile(r"[㐀-鿿]")
LATIN = re.compile(r"[A-Za-z]")


def needs_translation(u):
    """voice lines are asset paths; punctuation-only lines carry no language."""
    if u["who"] == "voice":
        return False
    s = u["src"]
    return bool(CJK.search(s) or LATIN.search(s))


def chunk(units, outdir, per):
    os.makedirs(outdir, exist_ok=True)
    # group by file so a chunk never straddles two scripts
    by_file = {}
    skipped = 0
    for i, u in enumerate(units):
        u["_i"] = i
        if not needs_translation(u):
            skipped += 1
            continue
        by_file.setdefault(u["file"], []).append(u)
    print(f"skipped {skipped} non-text units (voice paths / punctuation only)")
    n = 0
    manifest = []
    for rel, us in by_file.items():
        for start in range(0, len(us), per):
            part = us[start:start + per]
            n += 1
            name = f"chunk_{n:03d}.json"
            payload = [dict({"i": u["_i"], "who": u["who"], "src": u["src"]},
                            **({"ja": u["ja"]} if u.get("ja") else {})) for u in part]
            with open(os.path.join(outdir, name), "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=1)
            manifest.append({"chunk": name, "file": rel, "count": len(part),
                             "chars": sum(len(u["src"]) for u in part)})
    with open(os.path.join(outdir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    print(f"{n} chunks -> {outdir}")
    for m in manifest:
        print(f"  {m['chunk']}  {m['file']:26s} {m['count']:4d} units {m['chars']:6d} chars")


def collect(units, chunkdir, out):
    done = 0
    for fn in sorted(os.listdir(chunkdir)):
        if not fn.startswith("chunk_") or not fn.endswith(".out.json"):
            continue
        data = json.load(open(os.path.join(chunkdir, fn), encoding="utf-8"))
        for row in data:
            i = row["i"]
            if row.get("dst"):
                units[i]["dst"] = row["dst"]
                done += 1
    json.dump(units, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"collected {done}/{len(units)} translations -> {out}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "extract":
        us = extract(sys.argv[2])
        json.dump(us, open(sys.argv[3], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"{len(us)} units ({sum(1 for u in us if u['kind']=='string')} strings)")
    elif cmd == "apply":
        us = json.load(open(sys.argv[3], encoding="utf-8"))
        apply(sys.argv[2], us, sys.argv[4])
    elif cmd == "chunk":
        us = json.load(open(sys.argv[2], encoding="utf-8"))
        chunk(us, sys.argv[3], int(sys.argv[4]))
    elif cmd == "collect":
        us = json.load(open(sys.argv[2], encoding="utf-8"))
        collect(us, sys.argv[3], sys.argv[4])
