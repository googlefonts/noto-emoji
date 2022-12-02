"""Removes regional indicators from a font."""

from fontTools import subset
from fontTools import ttLib
import functools
from pathlib import Path
import sys
from typing import Set


def codepoints(font: ttLib.TTFont) -> Set[int]:
    unicode_cmaps = (t.cmap.keys() for t in font['cmap'].tables if t.isUnicode())
    return functools.reduce(lambda acc, u: acc | u, unicode_cmaps, set())


def is_regional_indicator(cp: int) -> bool:
    return 0x1F1E6 <= cp <= 0x1F1FF


def main(argv):
    for font_file in sorted(argv[1:]):
        font_file = Path(font_file)
        assert font_file.is_file(), font_file
        noflags_file = font_file.with_stem(font_file.stem + "-noflags")

        if noflags_file.is_file():
            print(font_file, "already has", noflags_file, "; nop")
            continue

        font = ttLib.TTFont(font_file)

        cps = codepoints(font)
        cps_without_flags = {cp for cp in cps if not is_regional_indicator(cp)}

        if cps == cps_without_flags:
            print(font_file, "has no regional indicators")
            continue

        subsetter = subset.Subsetter()
        subsetter.populate(unicodes=cps_without_flags)
        subsetter.subset(font)

        font.save(noflags_file)
        print(font_file, "=>" , noflags_file)


if __name__ == '__main__':
  main(sys.argv)
