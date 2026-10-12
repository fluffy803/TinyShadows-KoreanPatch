# -*- coding: utf-8 -*-
"""Release zip from the staged patch (run build_mod.py first).

  python tools/build_release.py <version>
    -> dist/TinyShadows_KoreanPatch_v<version>.zip  (game/...)
"""
import os, sys, zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE = os.environ.get("TS_WORKSPACE") or os.path.dirname(REPO)
STAGE = os.path.join(WORKSPACE, "mod")


def main():
    ver = sys.argv[1]
    out = os.path.join(REPO, "dist", f"TinyShadows_KoreanPatch_v{ver}.zip")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    n = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for root, _, fs in os.walk(STAGE):
            for fn in sorted(fs):
                p = os.path.join(root, fn)
                z.write(p, "game/" + os.path.relpath(p, STAGE).replace(os.sep, "/"))
                n += 1
    print(f"{out}: {n} files, {os.path.getsize(out) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
