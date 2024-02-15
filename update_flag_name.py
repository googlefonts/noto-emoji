"""Updates the name table for the CBDT flagsonly font."""

from fontTools import subset
from fontTools import ttLib
import functools
from pathlib import Path
import sys
from typing import Set


NAME_ID_FAMILY = 1
NAME_ID_UNIQUE_ID = 3
NAME_ID_FULLNAME = 4
NAME_ID_POSTSCRIPT_NAME = 6


_NAME_VALUES = [
    (NAME_ID_FAMILY, "Noto Color Emoji Flags"),
    (NAME_ID_UNIQUE_ID, "Noto Color Emoji Flags"),
    (NAME_ID_FULLNAME, "Noto Color Emoji Flags"),
    (NAME_ID_POSTSCRIPT_NAME, "NotoColorEmojiFlags"),
]


def main(argv):
    font_file = "fonts/NotoColorEmoji-flagsonly.ttf"
    font = ttLib.TTFont(font_file)
    name_table = font["name"]
    for (name_id, value) in _NAME_VALUES:
        name = name_table.getName(name_id, 3, 1, 0x409)
        name.string = value
    font.save(font_file)


if __name__ == '__main__':
  main(sys.argv)
