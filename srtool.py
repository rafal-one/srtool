#!/usr/bin/env python3
"""srtool: shift, rescale, merge, renumber and clean .srt subtitle files. Stdlib only."""
import argparse, re, sys

TS = re.compile(r"(\d+):(\d\d):(\d\d)[,.](\d{1,3})")
LINE = re.compile(r"(\S+)\s*-->\s*(\S+)(.*)")


def parse_ts(s):
    m = TS.fullmatch(s)
    if not m:
        raise ValueError(f"bad timestamp: {s!r}")
    h, mi, se, ms = m.groups()
    return ((int(h) * 60 + int(mi)) * 60 + int(se)) * 1000 + int(ms.ljust(3, "0"))


def fmt_ts(ms):
    ms = max(0, int(round(ms)))
    h, r = divmod(ms, 3600000)
    m, r = divmod(r, 60000)
    s, ms = divmod(r, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def parse(text):
    """Return list of [start_ms, end_ms, text]. Tolerates BOM, CRLF, missing indexes."""
    text = text.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")
    subs = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = block.split("\n")
        for i, l in enumerate(lines):
            m = LINE.match(l.strip())
            if m:
                subs.append([parse_ts(m.group(1)), parse_ts(m.group(2)), "\n".join(lines[i + 1:])])
                break
    return subs


def render(subs):
    subs = sorted(subs, key=lambda s: s[0])
    return "".join(f"{i}\n{fmt_ts(a)} --> {fmt_ts(b)}\n{t}\n\n" for i, (a, b, t) in enumerate(subs, 1))


def shift(subs, ms):
    return [[a + ms, b + ms, t] for a, b, t in subs]


def rescale(subs, factor):
    return [[a * factor, b * factor, t] for a, b, t in subs]


def sync(subs, t1_old, t1_new, t2_old, t2_new):
    """Linear map so that t1_old->t1_new and t2_old->t2_new (fixes drift / fps mismatch)."""
    if t2_old == t1_old:
        raise ValueError("sync: the two old timestamps must differ")
    k = (t2_new - t1_new) / (t2_old - t1_old)
    return [[t1_new + (a - t1_old) * k, t1_new + (b - t1_old) * k, t] for a, b, t in subs]


def merge(a, b, offset=0):
    return a + shift(b, offset)


def clean(subs):
    """Drop empty cues, strip HTML tags, fix end<start, collapse overlaps."""
    out = []
    for a, b, t in sorted(subs, key=lambda s: s[0]):
        t = re.sub(r"</?[a-zA-Z][^>]*>", "", t).strip()
        if not t:
            continue
        if b < a:
            b = a + 1000
        if out and out[-1][1] > a:
            out[-1][1] = a
        out.append([a, b, t])
    return out


def main(argv=None):
    p = argparse.ArgumentParser(prog="srtool", description=__doc__)
    sp = p.add_subparsers(dest="cmd", required=True)
    for name in ("shift", "rescale", "sync", "merge", "clean", "renumber"):
        s = sp.add_parser(name)
        s.add_argument("input")
        s.add_argument("-o", "--output", help="default: stdout")
        if name == "shift":
            s.add_argument("seconds", type=float, help="e.g. 2.5 or -1.2")
        if name == "rescale":
            s.add_argument("factor", type=float, help="e.g. 1.04271 (25/23.976)")
        if name == "sync":
            s.add_argument("t1_old"); s.add_argument("t1_new"); s.add_argument("t2_old"); s.add_argument("t2_new")
        if name == "merge":
            s.add_argument("other"); s.add_argument("--offset", type=float, default=0.0, help="seconds added to other")
    a = p.parse_args(argv)
    try:
        return _run(a)
    except (OSError, ValueError) as e:
        print(f"srtool: error: {e}", file=sys.stderr)
        return 2


def _run(a):
    read = lambda f: parse(open(f, encoding="utf-8-sig", errors="replace").read())
    subs = read(a.input)
    if a.cmd == "shift": subs = shift(subs, a.seconds * 1000)
    elif a.cmd == "rescale": subs = rescale(subs, a.factor)
    elif a.cmd == "sync": subs = sync(subs, *[parse_ts(x) for x in (a.t1_old, a.t1_new, a.t2_old, a.t2_new)])
    elif a.cmd == "merge": subs = merge(subs, read(a.other), a.offset * 1000)
    elif a.cmd == "clean": subs = clean(subs)
    out = render(subs)
    if a.output:
        open(a.output, "w", encoding="utf-8").write(out)
    else:
        sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
