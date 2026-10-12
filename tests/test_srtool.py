import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import srtool

SRC = "﻿1\r\n00:00:01,000 --> 00:00:02,500\r\n<i>Hello</i>\r\n\r\n2\r\n00:00:03,000 --> 00:00:04,000\r\nWorld\r\n"

def test_roundtrip_and_shift():
    s = srtool.parse(SRC)
    assert s[0][:2] == [1000, 2500]
    out = srtool.render(srtool.shift(s, 1500))
    assert "00:00:02,500 --> 00:00:04,000" in out

def test_shift_clamps():
    assert srtool.fmt_ts(-5) == "00:00:00,000"

def test_clean_strips_tags():
    assert srtool.clean(srtool.parse(SRC))[0][2] == "Hello"

def test_sync_linear():
    s = srtool.sync([[1000, 2000, "a"], [3000, 4000, "b"]], 1000, 2000, 3000, 6000)
    assert s[0][0] == 2000 and s[1][0] == 6000

def test_merge_sorted():
    out = srtool.render(srtool.merge(srtool.parse(SRC), [[0, 500, "x"]]))
    assert out.startswith("1\n00:00:00,000")
