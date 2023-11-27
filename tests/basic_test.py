from fontTools import ttLib
from pathlib import Path
import pytest
import re

def test_consistent_version():
    fonts_dir = Path("fonts")
    assert fonts_dir.is_dir()

    name5_re = re.compile(r'^Version (\d+.\d+);GOOG;noto-emoji:\d+:[a-z0-9]+$')

    debug_versions = []
    versions = set()
    for font_file in fonts_dir.rglob("*.ttf"):
        font = ttLib.TTFont(font_file)
        head_ver = f"{font['head'].fontRevision:.03f}"
        versions.add(head_ver)
        debug_versions.append(f"{font_file.name} head {head_ver}")
        for name in font['name'].names:
            # name 5 is version
            if name.nameID != 5:
                continue
            if not name.isUnicode():
                continue
            match = name5_re.match(name.toUnicode())
            assert match is not None, f"{name.toUnicode()} is malformed"
            versions.add(match.group(1))
            debug_versions.append(f"{font_file.name} name {match.group(1)}")
    debug_versions = "\n".join(debug_versions)
    assert len(versions) == 1, f"Should have a consistent version, found\n{debug_versions}"

def test_consistent_fstype():
    fonts_dir = Path("fonts")
    assert fonts_dir.is_dir()

    name5_re = re.compile(r'^Version (\d+.\d+);GOOG;noto-emoji:\d+:[a-z0-9]+$')

    debug_fstypes = []
    fstypes = set()
    for font_file in fonts_dir.rglob("*.ttf"):
        font = ttLib.TTFont(font_file)
        fstype = font['OS/2'].fsType
        fstypes.add(fstype)
        debug_fstypes.append(f"{font_file.name} fsType {fstype}")
    debug_fstypes = "\n".join(debug_fstypes)
    assert fstypes == {0}, f"All fsType's should be 0, found\n{debug_fstypes}"

def test_has_emojicompat():
    fonts_dir = Path("fonts")
    assert fonts_dir.is_dir()

    ec_fonts = set(fonts_dir.rglob("*-emojicompat.ttf"))
    assert {f.name for f in ec_fonts} == {"Noto-COLRv1-emojicompat.ttf", "NotoColorEmoji-emojicompat.ttf"}

    for font_file in ec_fonts:
        font = ttLib.TTFont(font_file)
        assert "meta" in font, f"{font_file.name} should have a meta table"
        assert "Emji" in font["meta"].data, f"{font_file.name} should have emojicompat data"
