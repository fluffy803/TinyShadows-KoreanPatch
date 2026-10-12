# -*- coding: utf-8 -*-
"""Assemble the Korean patch from the translated chunks.

  python build_mod.py            # collect -> apply -> compile -> stage mod/
  python build_mod.py --install  # ...and copy the staged files into the game

Only additive files are produced; the original *.rpa archives are never touched.
"""
import os, sys, io, json, shutil, subprocess

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

W = os.environ.get("TS_WORKSPACE") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(W, "tools")
WORK = os.path.join(W, "work")
CHUNKS = os.path.join(WORK, "chunks")
TL_SRC = os.path.join(W, "tl_korean")
PROJ = os.path.join(W, "proj")
PROJ_TL = os.path.join(PROJ, "game", "tl", "korean")
MOD_SRC = os.path.join(W, "mod_src")
IMG_SRC = os.path.join(W, "이미지번역", "번역본")   # optional: tl/korean/... image tree
STAGE = os.path.join(W, "mod")
GAME = os.environ.get("TS_GAME_DIR") or (
    r"C:\Program Files (x86)\Steam\steamapps\common\小小的身影，重叠的内心\game")

sys.path.insert(0, TOOLS)
import units as U


def run(*args, cwd=None):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if p.stdout:
        print(p.stdout.rstrip())
    if p.returncode != 0:
        print(p.stderr.rstrip())
        sys.exit(f"command failed: {args}")


def copy_tree(src, dst, keep=lambda fn: True):
    n = 0
    for root, _, files in os.walk(src):
        for fn in files:
            if not keep(fn):
                continue
            rel = os.path.relpath(os.path.join(root, fn), src)
            out = os.path.join(dst, rel)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            shutil.copy(os.path.join(root, fn), out)
            n += 1
    return n


def main():
    install = "--install" in sys.argv

    # 1. collect the per-chunk translations back into the unit list
    us = json.load(open(os.path.join(WORK, "units.json"), encoding="utf-8"))
    out = os.path.join(WORK, "units_translated.json")
    U.collect(us, CHUNKS, out)
    us = json.load(open(out, encoding="utf-8"))

    todo = [u for u in us if U.needs_translation(u) and not u.get("dst")]
    if todo:
        print(f"!! {len(todo)} units still untranslated "
              f"(they will stay in the original language)")

    # 2. write the translations into the tl tree
    U.apply(TL_SRC, us, PROJ_TL)

    # 3. drop the patch script in and compile everything to .rpyc
    for fn in os.listdir(MOD_SRC):
        if fn.endswith(".rpy"):
            shutil.copy(os.path.join(MOD_SRC, fn), os.path.join(PROJ, "game", fn))
    print("compiling...")
    run(os.path.join(PROJ, "lib", "py3-windows-x86_64", "python.exe"),
        "TinyShadowsInterwovenHearts.py", ".", "compile", cwd=PROJ)

    # 4. stage exactly the files the game needs
    if os.path.exists(STAGE):
        shutil.rmtree(STAGE)
    n = copy_tree(PROJ_TL, os.path.join(STAGE, "tl", "korean"),
                  keep=lambda fn: fn.endswith(".rpyc"))
    print(f"staged {n} compiled translation files")

    for fn in os.listdir(MOD_SRC):
        if not fn.endswith(".rpy"):
            continue
        rpyc = os.path.join(PROJ, "game", fn + "c")
        if not os.path.exists(rpyc):
            sys.exit(f"missing compiled patch: {rpyc}")
        shutil.copy(rpyc, os.path.join(STAGE, fn + "c"))
        print(f"staged {fn}c")

    # language label shown in the settings screen
    n = copy_tree(os.path.join(MOD_SRC, "gui"),
                  os.path.join(STAGE, "gui", "custom", "system", "setting"))
    print(f"staged {n} UI images")

    # 4a. audio-drama lyrics: one Korean text, written with the timings of both
    #     voice tracks (abc.lrc = Chinese voice, abc_jp.lrc = Japanese voice).
    #     .lrc is looked up by *text* language, so tl/korean/ wins when Korean is on.
    lyr = os.path.join(CHUNKS, "lyrics.out.json")
    if os.path.exists(lyr):
        ko = {r["i"]: r["dst"] for r in json.load(open(lyr, encoding="utf-8")) if r.get("dst")}
        for fn in ("abc.lrc", "abc_jp.lrc"):
            src = os.path.join(W, "extracted", "audio", "asmr", fn)
            out, i = [], 0
            for line in open(src, encoding="utf-8-sig").read().splitlines():
                if line.startswith("[") and "]" in line:
                    tag = line[:line.index("]") + 1]
                    line = tag + ko.get(i, line[len(tag):].strip())
                    i += 1
                out.append(line)
            dst = os.path.join(STAGE, "tl", "korean", "audio", "asmr", fn)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "w", encoding="utf-8") as f:
                f.write("\n".join(out) + "\n")
        print(f"staged lyrics ({len(ko)}/80 lines translated) x2")

    # 4b. translated images (tl/korean/<same path as original>), if any
    if os.path.isdir(IMG_SRC):
        n = copy_tree(IMG_SRC, os.path.join(STAGE, "tl", "korean"))
        print(f"staged {n} translated images")

    # 5. optionally install
    if install:
        if not os.path.isdir(GAME):
            sys.exit(f"game folder not found: {GAME}")
        copied = copy_tree(STAGE, GAME)
        print(f"installed {copied} files -> {GAME}")
    else:
        print(f"\nstaged in {STAGE} (run with --install to copy into the game)")


if __name__ == "__main__":
    main()
