"""Utility to add border and soft-light effects to NotoColorEmoji-COLRv1 region flags."""
import sys
import subprocess
from fontTools import ttLib
from fontTools.ttLib.tables import otTables as ot
from fontTools.colorLib.builder import LayerListBuilder
from nototools import font_data
from flag_glyph_name import flag_code_to_glyph_name
from map_pua_emoji import get_glyph_name_from_gsub


# In the CBDT font, the following flags only get no border:
# https://github.com/rsheeter/warp/issues/20
BORDERLESS_FLAGS = (
    "GF",
    "MQ",
    "NP",
    "PM",
)

# The two glyphs representing respectively the flag's border and the soft-light
# effect are expected to be c'mapped to the following PUA codepoint:
BORDER_CODEPOINT = 0x100000
SOFT_LIGHT_CODEPOINT = 0x100001


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


def _paint_colr_glyph(glyph_name):
    return _build_paint({"Format": ot.PaintFormat.PaintColrGlyph, "Glyph": glyph_name})


def _paint_composite(source, mode, backdrop):
    return _build_paint(
        {
            "Format": ot.PaintFormat.PaintComposite,
            "SourcePaint": source,
            "CompositeMode": mode,
            "BackdropPaint": backdrop,
        }
    )


def main():
    try:
        input_file, output_file = sys.argv[1:]
    except ValueError:
        print("usage: colrv1_add_border_to_flags.py INPUT_FONT OUTPUT_FONT")
        return 2

    font = ttLib.TTFont(input_file)

    if "COLR" not in font or font["COLR"].version != 1:
        print("error: missing required COLRv1 table")
        return 1

    cmap = font_data.get_cmap(font)
    try:
        border_name = cmap[BORDER_CODEPOINT]
        soft_light_name = cmap[SOFT_LIGHT_CODEPOINT]
    except KeyError as e:
        print(f"error: missing required PUA codepoint: {hex(e.args[0])}")
        return 1

    colr_glyphs = {
        rec.BaseGlyph: rec
        for rec in font["COLR"].table.BaseGlyphList.BaseGlyphPaintRecord
    }
    assert border_name in colr_glyphs
    assert soft_light_name in colr_glyphs

    regular_flags = []
    borderless_flags = []
    for flag_code in read_makefile_variable("SELECTED_FLAGS").split():
        flag_sequence = flag_code_to_sequence(flag_code)
        flag_name = get_glyph_name_from_gsub(flag_sequence, font)
        if flag_name is not None:
            flag = colr_glyphs[flag_name]
            if flag_code in BORDERLESS_FLAGS:
                borderless_flags.append(flag)
            else:
                regular_flags.append(flag)

    # For regular flags, first the border is multiplied onto the flag, then
    # the soft-light effect is applied to the result.
    for flag in regular_flags:
        flag.Paint = _paint_composite(
            source=_paint_colr_glyph(soft_light_name),
            mode=ot.CompositeMode.SOFT_LIGHT,
            backdrop=_paint_composite(
                source=flag.Paint,
                mode=ot.CompositeMode.MULTIPLY,
                backdrop=_paint_colr_glyph(border_name),
            ),
        )
    # borderless flags only get the soft-light effect
    for flag in borderless_flags:
        flag.Paint = _paint_composite(
            source=_paint_colr_glyph(soft_light_name),
            mode=ot.CompositeMode.SOFT_LIGHT,
            backdrop=flag.Paint,
        )

    font_data.delete_from_cmap(font, (BORDER_CODEPOINT, SOFT_LIGHT_CODEPOINT))

    font.save(output_file)


if __name__ == "__main__":
    sys.exit(main())
