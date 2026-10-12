# -*- coding: utf-8 -*-
"""Extract files from a ZiX-12A (RPA-3.0 variant) archive.

usage: rpa_extract.py <archive.rpa> <outdir> [substring-filter ...]
       (no filter = extract everything)
"""
import os, sys
from rpa_index import read_index

def main():
    rpa, outdir = sys.argv[1], sys.argv[2]
    filters = sys.argv[3:]
    index = read_index(rpa)
    n = 0
    total = 0
    with open(rpa, "rb") as f:
        for name, parts in sorted(index.items()):
            if filters and not any(x in name for x in filters):
                continue
            dst = os.path.join(outdir, name.replace("/", os.sep))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "wb") as o:
                for offset, dlen, start in parts:
                    if start:
                        o.write(start)
                    f.seek(offset)
                    o.write(f.read(dlen))
            n += 1
            total += os.path.getsize(dst)
            if n % 200 == 0:
                print(f"  {n} files, {total/1048576:.1f} MB", flush=True)
    print(f"done: {n} files, {total/1048576:.1f} MB -> {outdir}")

if __name__ == "__main__":
    main()
