"""Prints info about emoji fonts."""

from fontTools import ttLib
from pathlib import Path
import sys


def main():
    font_files = sorted(p for p in (Path(__file__).parent / "fonts").iterdir() if p.suffix == ".ttf")
    max_name_len = max(len(p.name) for p in font_files)

    for font_file in font_files:
        font = ttLib.TTFont(font_file)

        font_type = []
        if "CBDT" in font:
            font_type.append("CBDT")
        if "COLR" in font:
            font_type.append("COLR")
        if "meta" in font and "Emji" in font["meta"].data:
            font_type.append("EmojiCompat")
        font_type = ",".join(font_type)

        print(f"{font_file.name:{max_name_len + 1}} {font_type}")


if __name__ == '__main__':
  main()
