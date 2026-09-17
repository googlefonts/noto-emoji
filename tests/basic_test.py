from fontTools import ttLib
from pathlib import Path
import pytest
import re


NAME_ID_FAMILY = 1
NAME_ID_UNIQUE_ID = 3
NAME_ID_FULLNAME = 4
NAME_ID_POSTSCRIPT_NAME = 6


def test_consistent_version():
    for sub_dir in [Path("2D/fonts"), Path("3D/fonts")]:
        assert sub_dir.is_dir()

        name5_re = re.compile(r"^Version (\d+.\d+);GOOG;noto-emoji:\d+:[a-z0-9]+$")

        debug_versions = []
        versions = set()
        for font_file in sub_dir.rglob("*.ttf"):
            font = ttLib.TTFont(font_file)
            head_ver = f"{font['head'].fontRevision:.03f}"
            versions.add(head_ver)
            debug_versions.append(f"{font_file.name} head {head_ver}")
            for name in font["name"].names:
                # name 5 is version
                if name.nameID != 5:
                    continue
                if not name.isUnicode():
                    continue
                match = name5_re.match(name.toUnicode())
                assert match is not None, f"{name.toUnicode()} is malformed in {font_file.name}"
                versions.add(match.group(1))
                debug_versions.append(f"{font_file.name} name {match.group(1)}")
        debug_versions_str = "\n".join(debug_versions)
        assert (
            len(versions) == 1
        ), f"Should have a consistent version under {sub_dir}, found\n{debug_versions_str}"


def test_consistent_fstype():
    for sub_dir in [Path("2D/fonts"), Path("3D/fonts")]:
        assert sub_dir.is_dir()

        debug_fstypes = []
        fstypes = set()
        for font_file in sub_dir.rglob("*.ttf"):
            font = ttLib.TTFont(font_file)
            fstype = font["OS/2"].fsType
            fstypes.add(fstype)
            debug_fstypes.append(f"{font_file.name} fsType {fstype}")
        debug_fstypes_str = "\n".join(debug_fstypes)
        assert fstypes == {0}, f"All fsType's should be 0 under {sub_dir}, found\n{debug_fstypes_str}"


def test_has_emojicompat():
    fonts_dir = Path("2D/fonts")
    assert fonts_dir.is_dir()

    ec_fonts = set(fonts_dir.rglob("*-emojicompat.ttf"))
    assert {f.name for f in ec_fonts} == {
        "Noto-COLRv1-emojicompat.ttf",
        "NotoColorEmoji-emojicompat.ttf",
    }

    for font_file in ec_fonts:
        font = ttLib.TTFont(font_file)
        assert "meta" in font, f"{font_file.name} should have a meta table"
        assert (
            "Emji" in font["meta"].data
        ), f"{font_file.name} should have emojicompat data"


def name(font, name_id):
    values = set()
    for name in font["name"].names:
        if name.nameID == name_id:
            values.add(name.toUnicode())
    assert len(values) == 1, f"{name_id} has multiple definitions: {values}"
    return next(iter(values))


def test_flagsonly_name():
    found = False
    for sub_dir in [Path("2D/fonts"), Path("3D/fonts")]:
        assert sub_dir.is_dir()
        for font_file in sub_dir.rglob("*flagsonly.ttf"):
            found = True
            font = ttLib.TTFont(font_file)
            assert [
                "Noto Color Emoji Flags",
                "Noto Color Emoji Flags",
                "Noto Color Emoji Flags",
                "NotoColorEmojiFlags",
            ] == [
                name(font, NAME_ID_FAMILY),
                name(font, NAME_ID_FULLNAME),
                name(font, NAME_ID_UNIQUE_ID),
                name(font, NAME_ID_POSTSCRIPT_NAME),
            ]
    assert found, "Should find at least one flagsonly font to test"
