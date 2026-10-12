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


import pytest

def _f(tmp_path, text=SRC, name="a.srt"):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return str(p)

def test_parse_ts_variants():
    assert srtool.parse_ts("00:00:01.5") == 1500
    assert srtool.parse_ts("01:02:03,004") == 3723004

def test_parse_ts_bad():
    with pytest.raises(ValueError):
        srtool.parse_ts("1:2")

def test_fmt_ts_hours():
    assert srtool.fmt_ts(3723004) == "01:02:03,004"

def test_parse_missing_index_and_multiline():
    s = srtool.parse("00:00:01,000 --> 00:00:02,000\nline1\nline2\n")
    assert s == [[1000, 2000, "line1\nline2"]]

def test_parse_empty():
    assert srtool.parse("") == []

def test_rescale():
    assert srtool.rescale([[1000, 2000, "a"]], 2) == [[2000, 4000, "a"]]

def test_sync_zero_divisor():
    with pytest.raises(ValueError):
        srtool.sync([[0, 1, "a"]], 5, 5, 5, 9)

def test_clean_drops_empty_and_fixes_end():
    out = srtool.clean([[1000, 500, "x"], [2000, 3000, "<b></b>"]])
    assert out == [[1000, 2000, "x"]]

def test_clean_overlap():
    out = srtool.clean([[0, 3000, "a"], [2000, 4000, "b"]])
    assert out[0][1] == 2000

def test_renumber_render_sorts():
    out = srtool.render([[5000, 6000, "b"], [1000, 2000, "a"]])
    assert out.startswith("1\n00:00:01,000")

def test_cli_shift_stdout(tmp_path, capsys):
    assert srtool.main(["shift", _f(tmp_path), "1"]) == 0
    assert "00:00:02,000 --> 00:00:03,500" in capsys.readouterr().out

def test_cli_output_file(tmp_path):
    o = tmp_path / "o.srt"
    assert srtool.main(["clean", _f(tmp_path), "-o", str(o)]) == 0
    assert "Hello" in o.read_text() and "<i>" not in o.read_text()

def test_cli_merge_offset(tmp_path, capsys):
    b = _f(tmp_path, "1\n00:00:00,000 --> 00:00:01,000\nB\n", "b.srt")
    srtool.main(["merge", _f(tmp_path), b, "--offset", "10"])
    assert "00:00:10,000" in capsys.readouterr().out

def test_cli_missing_file(tmp_path, capsys):
    assert srtool.main(["shift", str(tmp_path / "nope.srt"), "1"]) == 2
    assert "error" in capsys.readouterr().err

def test_cli_bad_sync_ts(tmp_path, capsys):
    assert srtool.main(["sync", _f(tmp_path), "x", "1", "2", "3"]) == 2

def test_cli_no_command():
    with pytest.raises(SystemExit) as e:
        srtool.main([])
    assert e.value.code == 2
