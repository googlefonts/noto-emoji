"""Utility to add soft-light effect to NotoColorEmoji-COLRv1 region flags."""
import sys
import subprocess
from fontTools import ttLib
from fontTools.ttLib.tables import otTables as ot
from fontTools.ttLib.tables.C_P_A_L_ import Color
from fontTools.colorLib.builder import LayerListBuilder
from flag_glyph_name import flag_code_to_glyph_name
from map_pua_emoji import get_glyph_name_from_gsub


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

    colr_glyphs = {
        rec.BaseGlyph: rec
        for rec in font["COLR"].table.BaseGlyphList.BaseGlyphPaintRecord
    }
    cpal = font["CPAL"]

    for flag_code in read_makefile_variable("SELECTED_FLAGS").split():
        flag_sequence = flag_code_to_sequence(flag_code)
        flag_name = get_glyph_name_from_gsub(flag_sequence, font)
        if flag_name is not None:
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

    font.save(output_file)


if __name__ == "__main__":
    sys.exit(main())
