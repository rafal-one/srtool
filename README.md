# srtool

Install: `pip install srtool-cli` (command: `srtool`)

Zero-dependency Python CLI to fix `.srt` subtitles: shift, rescale (fps change), two-point sync (drift), merge, clean, renumber.

```
python3 srtool.py shift movie.srt -1.5 -o fixed.srt        # 1.5 s earlier
python3 srtool.py rescale movie.srt 1.04271 -o fixed.srt   # 23.976 -> 25 fps
python3 srtool.py sync movie.srt 00:01:00,000 00:01:02,000 01:30:00,000 01:30:09,000 -o fixed.srt
python3 srtool.py merge a.srt b.srt --offset 5400 -o both.srt
python3 srtool.py clean movie.srt -o clean.srt             # strip tags, drop empty cues, fix overlaps
```
Handles BOM, CRLF, missing indexes. Tests: `python3 -m pytest tests`.

## Support
If it saved you time, donations via PayPal: 4433@vp.pl

Donate: https://paypal.me/RafalBaranowski
