# -*- coding: utf-8 -*-
"""RPA-3.0 index reader.  usage: rpa_index.py <archive.rpa>  (lists entries)"""
import sys, zlib, pickle

def read_index(path):
    with open(path, "rb") as f:
        head = f.readline().split()
        assert head[0] == b"RPA-3.0", head[:1]
        offset = int(head[1], 16)
        key = int(head[2], 16)
        f.seek(offset)
        index = pickle.loads(zlib.decompress(f.read()))

    def to_bytes(s):
        if not s:
            return b""
        if not isinstance(s, bytes):
            s = s.encode("latin-1")
        return s

    for k in list(index.keys()):
        if len(index[k][0]) == 2:
            index[k] = [(o ^ key, d ^ key, b"") for o, d in index[k]]
        else:
            index[k] = [(o ^ key, d ^ key, to_bytes(st)) for o, d, st in index[k]]
    return index

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    for name, parts in sorted(read_index(sys.argv[1]).items()):
        print(sum(p[1] for p in parts), name)

if __name__ == "__main__":
    main()
