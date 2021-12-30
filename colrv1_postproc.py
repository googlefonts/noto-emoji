"""
Post-nanoemoji processing of the Noto COLRv1 Emoji file.

For now substantially based on copying from a correct bitmap build.
"""
from absl import app
from fontTools import ttLib
import map_pua_emoji
from nototools import add_vs_cmap
from nototools import unicode_data


def _is_colrv1(font):
  return (
    "COLR" in font
    and font["COLR"].version == 1
  )


def _is_cbdt(font):
  return "CBDT" in font


def _is_compat_font(font):
  return (
    "meta" in font
    and "Emji" in font["meta"].data
  )


def _copy_emojicompat_data(colr_font, cbdt_font):
    colr_font["meta"] = cbdt_font["meta"]


def _set_name(name_table, nameID):
  name_table.getName(value, nameID, 3, 1, 0x409)


def _set_name(name_table, nameID, value):
  name_table.setName(value, nameID, 3, 1, 0x409)


def _copy_names(colr_font, cbdt_font):
  colr_font["name"] = cbdt_font["name"]
  name_table = colr_font["name"]
  assert all((n.platformID, n.platEncID, n.langID) == (3, 1, 0x409)
             for n in name_table.names), "Should only have names Android uses"

  # Amendments
  _set_name(name_table, 10, "Color emoji font using COLRv1.")
  _set_name(name_table, 11, "https://github.com/googlefonts/noto-emoji")
  _set_name(name_table, 12, "https://github.com/googlefonts/noto-emoji")


# CBDT build step: @$(VS_ADDER) -vs 2640 2642 2695 --dstdir '.' -o "$@-with-pua-varsel" "$@-with-pua"
def _add_vs_cmap(colr_font):
  emoji_variants = unicode_data.get_unicode_emoji_variants() | {0x2640, 0x2642, 0x2695}
  add_vs_cmap.modify_font("COLRv1 Emoji", colr_font, "emoji", emoji_variants)


def _is_variation_selector_cmap_table(table):
  assert table.format in {4, 12, 14}
  return table.format == 14


def _lookup_in_cmap(colr_font, codepoint):
  result = set()
  for table in colr_font["cmap"].tables:
    if _is_variation_selector_cmap_table(table):
      continue
    assert codepoint in table.cmap
    result.add(table.cmap[codepoint])
  assert len(result) == 1, f"Ambiguous mapping for {codepoint}: {result}"
  return next(iter(result))


def _map_flag_tag_chars_to_space(colr_font):
  gn_space = _lookup_in_cmap(colr_font, ord(" "))

  # Add all tag characters used in flags
  tag_cps = set(range(0xE0030, 0xE0039 + 1)) | set(range(0xE0061, 0xE007A + 1))

  # CBDT maps these things to space based on hb-shape testing
  # Android fontchain_lint is unhappy if no such mapping exists
  for table in colr_font["cmap"].tables:
    if _is_variation_selector_cmap_table(table):
      continue
    for cp in tag_cps:
      if not _is_bmp(cp) and table.format == 4:
        continue
      table.cmap[cp] = gn_space
      print(f"Map 0x{cp:04x} to space, format {table.format}")


def _is_bmp(cp):
  return cp in range(0x0000, 0xFFFF + 1)


def main(argv):
    if len(argv) != 3:
      raise ValueError("Must have two args, a COLRv1 font and a CBDT emojicompat font")

    colr_font = ttLib.TTFont(argv[1])
    if not _is_colrv1(colr_font):
      raise ValueError("First arg must be a COLRv1 font")

    cbdt_font = ttLib.TTFont(argv[2])
    if not _is_cbdt(cbdt_font) or not _is_compat_font(cbdt_font):
      raise ValueError("Second arg must be a CBDT emojicompat font")

    _copy_emojicompat_data(colr_font, cbdt_font)
    _copy_names(colr_font, cbdt_font)

    # CBDT build step: @$(PYTHON) $(PUA_ADDER) "$@" "$@-with-pua"
    map_pua_emoji.add_pua_cmap_to_font(colr_font)

    _add_vs_cmap(colr_font)

    _map_flag_tag_chars_to_space(colr_font)

    colr_font.save('fonts/Noto-COLRv1-noflags.ttf')


if __name__ == "__main__":
    app.run(main)