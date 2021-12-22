"""
Post-nanoemoji processing of the Noto COLRv1 Emoji file.

For now substantially based on copying from a correct bitmap build.
"""
from absl import app
from fontTools import ttLib


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

    colr_font.save('../fonts/Noto-COLRv1-noflags.ttf')


if __name__ == "__main__":
    app.run(main)