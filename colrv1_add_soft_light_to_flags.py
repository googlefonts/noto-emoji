"""Utility to add soft-light effect to NotoColorEmoji-COLRv1 region flags."""
import sys
import subprocess
from fontTools import ttLib
from fontTools.ttLib.tables import otTables as ot
from fontTools.ttLib.tables.C_P_A_L_ import Color
from fontTools.colorLib.builder import LayerListBuilder
from add_aliases import read_default_emoji_aliases
from flag_glyph_name import flag_code_to_glyph_name
from map_pua_emoji import get_glyph_name_from_gsub


REGIONAL_INDICATOR_RANGE = range(0x1F1E6, 0x1F1FF + 1)
BLACK_FLAG = 0x1F3F4
CANCEL_TAG = 0xE007F
TAG_RANGE = range(0xE0000, CANCEL_TAG + 1)


def is_flag(sequence):
    # regular region flags are comprised of regional indicators
    if all(cp in REGIONAL_INDICATOR_RANGE for cp in sequence):
        return True

    # subdivision flags start with  black flag, contain some tag characters and end with
    # a cancel tag
    if (
        len(sequence) > 2
        and sequence[0] == BLACK_FLAG
        and sequence[-1] == CANCEL_TAG
        and all(cp in TAG_RANGE for cp in sequence[1:-1])
    ):
        return True

    return False


def read_makefile_variable(var_name):
    # see `print-%` command in Makefile
    value = subprocess.run(
        ["make", f"print-{var_name}"], capture_output=True, check=True
    ).stdout.decode("utf-8")
    return value[len(var_name) + len(" = ") :].strip()


def flag_code_to_sequence(flag_code):
    # I use the existing code to first convert from flag code to glyph name,
    # and then convert names back to integer codepoints since it already
    # handles both the region indicators and subdivision tags.
    name = flag_code_to_glyph_name(flag_code)
    assert name.startswith("u")
    return tuple(int(v, 16) for v in name[1:].split("_"))


def all_flag_sequences():
    """Return the set of all noto-emoji's region and subdivision flag sequences.
    These include those in SELECTED_FLAGS Makefile variable plus those listed
    in the 'emoji_aliases.txt' file.
    """
    result = {
        flag_code_to_sequence(flag_code)
        for flag_code in read_makefile_variable("SELECTED_FLAGS").split()
    }
    result.update(seq for seq in read_default_emoji_aliases() if is_flag(seq))
    return result


_builder = LayerListBuilder()


def _build_paint(source):
    return _builder.buildPaint(source)


def _paint_composite(source, mode, backdrop):
    return _build_paint(
        {
            "Format": ot.PaintFormat.PaintComposite,
            "SourcePaint": source,
            "CompositeMode": mode,
            "BackdropPaint": backdrop,
        }
    )


def _palette_index(cpal, color):
    assert len(cpal.palettes) == 1
    palette = cpal.palettes[0]
    try:
        i = palette.index(color)
    except ValueError:
        i = len(palette)
        palette.append(color)
        cpal.numPaletteEntries += 1
        assert len(palette) == cpal.numPaletteEntries
    return i


WHITE = Color.fromHex("#FFFFFFFF")
GRAY = Color.fromHex("#808080FF")
BLACK = Color.fromHex("#000000FF")


def _soft_light_gradient(cpal):
    return _build_paint(
        {
            "Format": ot.PaintFormat.PaintLinearGradient,
            "ColorLine": {
                "Extend": "pad",
                "ColorStop": [
                    {
                        "StopOffset": 0.0,
                        "PaletteIndex": _palette_index(cpal, WHITE),
                        "Alpha": 0.5,
                    },
                    {
                        "StopOffset": 0.5,
                        "PaletteIndex": _palette_index(cpal, GRAY),
                        "Alpha": 0.5,
                    },
                    {
                        "StopOffset": 1.0,
                        "PaletteIndex": _palette_index(cpal, BLACK),
                        "Alpha": 0.5,
                    },
                ],
            },
            "x0": 47,
            "y0": 790,
            "x1": 890,
            "y1": -342,
            "x2": -1085,
            "y2": -53,
        },
    )


def flag_ligature_glyphs(font):
    """Yield ligature glyph names for all the region/subdivision flags in the font."""
    for flag_sequence in all_flag_sequences():
        flag_name = get_glyph_name_from_gsub(flag_sequence, font)
        if flag_name is not None:
            yield flag_name


def add_soft_light_to_flags(font, flag_glyph_names=None):
    """Add soft-light effect to region and subdivision flags in CORLv1 font."""
    if flag_glyph_names is None:
        flag_glyph_names = flag_ligature_glyphs(font)

    colr_glyphs = {
        rec.BaseGlyph: rec
        for rec in font["COLR"].table.BaseGlyphList.BaseGlyphPaintRecord
    }
    cpal = font["CPAL"]

    for flag_name in flag_glyph_names:
        flag = colr_glyphs[flag_name]
        flag.Paint = _paint_composite(
            source=_paint_composite(
                source=_soft_light_gradient(cpal),
                mode=ot.CompositeMode.SRC_IN,
                backdrop=flag.Paint,
            ),
            mode=ot.CompositeMode.SOFT_LIGHT,
            backdrop=flag.Paint,
        )


def main():
    try:
        input_file, output_file = sys.argv[1:]
    except ValueError:
        print("usage: colrv1_add_soft_light_to_flags.py INPUT_FONT OUTPUT_FONT")
        return 2

    font = ttLib.TTFont(input_file)

    if "COLR" not in font or font["COLR"].version != 1:
        print("error: missing required COLRv1 table")
        return 1

    add_soft_light_to_flags(font)

    font.save(output_file)


if __name__ == "__main__":
    sys.exit(main())
