# -*- coding: utf-8 -*-
"""Merge the strings-only tl tree (from decompiled sources) into the
dialogue tl tree (generated from the original compiled scripts)."""
import os, sys, re, shutil

W = os.environ.get("WT_WORKSPACE") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIALOGUE = os.path.join(W, "proj", "game", "tl", "korean")
STRINGS = os.path.join(W, "proj_src", "game", "tl", "korean")
OUT = os.path.join(W, "tl_korean")

STR_HDR = re.compile(r"^translate korean strings:\s*$", re.M)


def strings_block(path):
    """Return the `translate korean strings:` block of a generated file, or ''."""
    text = open(path, encoding="utf-8-sig").read()
    m = STR_HDR.search(text)
    if not m:
        return ""
    return text[m.start():].rstrip() + "\n"


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    shutil.copytree(DIALOGUE, OUT)
    for f in list(os.walk(OUT)):
        pass
    # drop the stray compiled file the runtime left behind
    for root, _, files in os.walk(OUT):
        for fn in files:
            if fn.endswith(".rpyc"):
                os.remove(os.path.join(root, fn))

    merged, added = 0, 0
    for root, _, files in os.walk(STRINGS):
        for fn in files:
            if not fn.endswith(".rpy"):
                continue
            src = os.path.join(root, fn)
            rel = os.path.relpath(src, STRINGS)
            dst = os.path.join(OUT, rel)
            block = strings_block(src)
            if not block:
                continue
            if rel == "common.rpy":
                continue  # already present, identical scan
            if os.path.exists(dst):
                with open(dst, "a", encoding="utf-8") as o:
                    o.write("\n" + block)
                merged += 1
            else:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                with open(dst, "w", encoding="utf-8") as o:
                    o.write("\ufeff# TODO: Translation updated\n\n" + block)
                added += 1
    print(f"merged strings into {merged} files, created {added} new files")

    n_dlg = n_str = 0
    for root, _, files in os.walk(OUT):
        for fn in files:
            if not fn.endswith(".rpy"):
                continue
            t = open(os.path.join(root, fn), encoding="utf-8-sig").read()
            n_dlg += len(re.findall(r"^translate korean \w+:", t, re.M))
            n_str += len(re.findall(r"^    old ", t, re.M))
    print(f"total: {n_dlg} dialogue units, {n_str} strings -> {OUT}")


if __name__ == "__main__":
    main()
