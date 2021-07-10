#!/usr/bin/env python3
# Copyright 2021 Google, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Google Author(s): Rod Sheeter

import argparse
import contextlib
from fontTools import ttLib
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables import sbixStrike
from fontTools.ttLib.tables import sbixGlyph
from nototools import tool_utils

# https://docs.microsoft.com/en-us/typography/opentype/spec/cbdt#glyph-bitmap-data-formats
_CBDT_FORMAT_SMALL_METRIC_PNG = 17

def _del_table(font, tag):
  if tag in font:
    del font[tag]

def _make_sbix(cblc, cbdt):
  # Ref https://gist.github.com/anthrotype/8c08eb372df2fb5da311887b32c2b9ac
  sbix = ttLib.newTable("sbix")

  # Apple Emoji uses this
  resolution = 72

  # Noto CBLC will tell you 109 ppem but that makes the sbix assets seem too big
  ppem = 128
  sbix_strike = sbixStrike.Strike(ppem=ppem, resolution=resolution)
  sbix.strikes[sbix_strike.ppem] = sbix_strike

  for strike in cbdt.strikeData:
    for glyph_name, cbdt_bitmap in strike.items():
      cbdt_bitmap.decompile()  # populate .metrics, .imageData

      assert cbdt_bitmap.getFormat() in {_CBDT_FORMAT_SMALL_METRIC_PNG}  # only format for now

      sbix_strike.glyphs[glyph_name] = sbixGlyph.Glyph(
        glyphName=glyph_name,
        graphicType="png",
        imageData=cbdt_bitmap.imageData,
        # Apple Color Emoji seem to always be 0
        # but then our glyphs are too high
        originOffsetY=-20,
        #originOffsetX=cbdt_bitmap.metrics.BearingX,
        #originOffsetY=cbdt_bitmap.metrics.BearingY,
      )

  return sbix


def _add_empty_glyf_glyphs(font):
    pen = TTGlyphPen(None)
    empty_glyph = pen.glyph()
    font['loca'] = ttLib.newTable("loca")
    font['glyf'] = glyf_table = ttLib.newTable("glyf")
    glyf_table.glyphOrder = font.getGlyphOrder()
    glyf_table.glyphs = {g: empty_glyph for g in glyf_table.glyphOrder}


def main():
  parser = argparse.ArgumentParser(
      description="Creates an SBIX (Apple style) bitmap font from a CBDT (Google style) bitmap font.")
  parser.add_argument(
      '-i', '--in_file', help='Input file', default="fonts/NotoColorEmoji.ttf")
  parser.add_argument(
      '-o', '--out_file', help='Output file', default="fonts/NotoColorEmoji_AppleCompatible.ttf")
  args = parser.parse_args()

  with contextlib.closing(ttLib.TTFont(args.in_file)) as font:
    font["sbix"] = _make_sbix(font["CBLC"], font["CBDT"])

    _add_empty_glyf_glyphs(font)

    _del_table(font, "CBDT")
    _del_table(font, "CBLC")

    print(f"Writing {args.out_file}...")
    font.save(args.out_file)

if __name__ == '__main__':
  main()