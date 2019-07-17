#!/usr/bin/env python3
# Copyright 2015 Google, Inc. All Rights Reserved.
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
# Google Author(s): Doug Felt

"""Tool to update GSUB, hmtx, cmap, glyf tables with svg image glyphs."""
from __future__ import print_function

import argparse
import glob
import logging
import os
import re
import sys

from fontTools.ttLib.tables import otTables
from fontTools.ttLib.tables import _g_l_y_f
from fontTools.ttLib.tables import S_V_G_ as SVG
from fontTools import ttx

from nototools import tool_utils

import add_emoji_gsub
import svg_builder


class FontBuilder(object):
  """A utility for mutating a ttx font.  This maintains glyph_order, cmap, and
  hmtx tables, and optionally GSUB, glyf, and SVN tables as well."""

  def __init__(self, font):
    self.font = font;
    self.glyph_order = font.getGlyphOrder()
    self.cmap = font['cmap'].tables[0].cmap
    self.hmtx = font['hmtx'].metrics

  def init_gsub(self):
    """Call this if you are going to add ligatures to the font.  Creates a GSUB
    table if there isn't one already."""

    if hasattr(self, 'ligatures'):
      return
    font = self.font
    if 'GSUB' not in font:
      ligature_subst = otTables.LigatureSubst()
      ligature_subst.ligatures = {}

      lookup = otTables.Lookup()
      lookup.LookupType = 4
      lookup.LookupFlag = 0
      lookup.SubTableCount = 1
      lookup.SubTable = [ligature_subst]

      font['GSUB'] = add_emoji_gsub.create_simple_gsub([lookup])
    else:
      lookup = font['GSUB'].table.LookupList.Lookup[0]
      assert lookup.LookupType == 4
      assert lookup.LookupFlag == 0
    self.ligatures = lookup.SubTable[0].ligatures

  def init_glyf(self):
    """Call this if you need to create empty glyf entries in the font when you
    add a new glyph."""

    if hasattr(self, 'glyphs'):
      return
    font = self.font
    if 'glyf' not in font:
      glyf_table = _g_l_y_f.table__g_l_y_f()
      glyf_table.glyphs = {}
      glyf_table.glyphOrder = self.glyph_order
      font['glyf'] = glyf_table
    self.glyphs = font['glyf'].glyphs

  def init_svg(self):
    """Call this if you expect to add SVG images in the font. This calls
    init_glyf since SVG support currently requires fallback glyf records for
    each SVG image."""

    if hasattr(self, 'svgs'):
      return

    # svg requires glyf
    self.init_glyf()

    font = self.font
    if 'SVG ' not in font:
      svg_table = SVG.table_S_V_G_()
      svg_table.docList = []
      svg_table.colorPalettes = None
      font['SVG '] = svg_table
    self.svgs = font['SVG '].docList

  def glyph_name(self, string):
    return "_".join(["u%04X" % ord(char) for char in string])

  def glyph_name_to_index(self, name):
    return self.glyph_order.index(name) if name in self.glyph_order else -1;

  def glyph_index_to_name(self, glyph_index):
    if glyph_index < len(self.glyph_order):
      return self.glyph_order[glyph_index]
    return ''

  def have_glyph(self, name):
    return self.name_to_glyph_index >= 0

  def _add_ligature(self, glyphstr):
    lig = otTables.Ligature()
    lig.CompCount = len(glyphstr)
    lig.Component = [self.glyph_name(ch) for ch in glyphstr[1:]]
    lig.LigGlyph = self.glyph_name(glyphstr)

    first = self.glyph_name(glyphstr[0])
    try:
      self.ligatures[first].append(lig)
    except KeyError:
      self.ligatures[first] = [lig]

  def _add_empty_glyph(self, glyphstr, name):
    """Create an empty glyph. If glyphstr is not a ligature, add a cmap entry
    for it."""
    if len(glyphstr) == 1:
      self.cmap[ord(glyphstr)] = name
    self.hmtx[name] = [0, 0]
    self.glyph_order.append(name)
    if hasattr(self, 'glyphs'):
      self.glyphs[name] = _g_l_y_f.Glyph()

  def add_components_and_ligature(self, glyphstr):
    """Convert glyphstr to a name and check if it already exists. If not, check
    if it is a ligature (longer than one codepoint), and if it is, generate
    empty glyphs with cmap entries for any missing ligature components and add a
    ligature record.  Then generate an empty glyph for the name.  Return a tuple
    with the name, index, and a bool indicating whether the glyph already
    existed."""

    name = self.glyph_name(glyphstr)
    index = self.glyph_name_to_index(name)
    exists = index >= 0
    if not exists:
      if len(glyphstr) > 1:
        for char in glyphstr:
          if ord(char) not in self.cmap:
            char_name = self.glyph_name(char)
            self._add_empty_glyph(char, char_name)
        self._add_ligature(glyphstr)
      index = len(self.glyph_order)
      self._add_empty_glyph(glyphstr, name)
    return name, index, exists

  def add_svg(self, doc, hmetrics, name, index):
    """Add an svg table entry. If hmetrics is not None, update the hmtx table.
    This expects the glyph has already been added."""
    # sanity check to make sure name and index correspond.
    assert name == self.glyph_index_to_name(index)
    if hmetrics:
      self.hmtx[name] = hmetrics
    svg_record = (doc, index, index) # startGlyphId, endGlyphId are the same
    self.svgs.append(svg_record)


def collect_glyphstr_file_pairs(prefix, ext, include=None, exclude=None, verbosity=1):
  """Scan files with the given prefix and extension, and return a list of
  (glyphstr, filename) where glyphstr is the character or ligature, and filename
  is the image file associated with it.  The glyphstr is formed by decoding the
  filename (exclusive of the prefix) as a sequence of hex codepoints separated
  by underscore. Include, if defined, is a regex string to include only matched
  filenames. Exclude, if defined, is a regex string to exclude matched
  filenames, and is applied after include."""

  image_files = {}
  glob_pat = "%s*.%s" % (prefix, ext)
  leading = len(prefix)
  trailing = len(ext) + 1 # include dot
  logging.info("Looking for images matching '%s'.", glob_pat)
  ex_count = 0
  ex = re.compile(exclude) if exclude else None
  inc = re.compile(include) if include else None
  if inc:
    logging.info("Including images matching '%s'.", include)
  if ex:
    logging.info("Excluding images matching '%s'.", exclude)

  for image_file in glob.glob(glob_pat):
    if inc and not inc.search(image_file):
      continue

    if ex and ex.search(image_file):
      if verbosity > 1:
        print("Exclude %s" % image_file)
      ex_count += 1
      continue

    codes = image_file[leading:-trailing]
    if "_" in codes:
      pieces = codes.split ("_")
      u = "".join ([unichr(int(code, 16)) for code in pieces])
    else:
      u = unichr(int(codes, 16))
    image_files[u] = image_file

  if ex_count:
    logging.info("Excluded %d files.", ex_count)
  if not image_files:
    raise Exception ("No image files matching '%s'.", glob_pat)
  logging.info("Matched %s files.", len(image_files))
  return image_files.items()


def sort_glyphstr_tuples(glyphstr_tuples):
  """The list contains tuples whose first element is a string representing a
  character or ligature.  It is sorted with shorter glyphstrs first, then
  alphabetically. This ensures that ligature components are added to the font
  before any ligatures that contain them."""
  glyphstr_tuples.sort(key=lambda t: (len(t[0]), t[0]))


def add_image_glyphs(in_file, out_file, pairs):
  """Add images from pairs (glyphstr, filename) to .ttx file in_file and write
  to .ttx file out_file."""

  font = ttx.TTFont()
  font.importXML(in_file)

  sort_glyphstr_tuples(pairs)

  font_builder = FontBuilder(font)
  # we've already sorted by length, so the longest glyphstrs are at the end. To
  # see if we have ligatures, we just need to check the last one.
  if len(pairs[-1][0]) > 1:
    font_builder.init_gsub()

  img_builder = svg_builder.SvgBuilder(font_builder)
  for glyphstr, filename in pairs:
    logging.debug("Adding glyph for U+%s", ",".join(
          ["%04X" % ord(char) for char in glyphstr]))
    img_builder.add_from_filename(glyphstr, filename)

  font.saveXML(out_file)
  logging.info("Added %s images to %s", len(pairs), out_file)


def main(argv):
  usage = """This will search for files that have image_prefix followed by one
  or more hex numbers (separated by underscore if more than one), and end in
  ".svg". For example, if image_prefix is "icons/u", then files with names like
  "icons/u1F4A9.svg" or "icons/u1F1EF_1F1F5.svg" will be loaded.  The script
  then adds cmap, htmx, and potentially GSUB entries for the Unicode characters
  found.  The advance width will be chosen based on image aspect ratio.  If
  Unicode values outside the BMP are desired, the existing cmap table should be
  of the appropriate (format 12) type.  Only the first cmap table and the first
  GSUB lookup (if existing) are modified."""

  parser = argparse.ArgumentParser(
      description='Update cmap, glyf, GSUB, and hmtx tables from image glyphs.',
      epilog=usage)
  parser.add_argument(
      'in_file', help='Input ttx file name.', metavar='fname')
  parser.add_argument(
      'out_file', help='Output ttx file name.', metavar='fname')
  parser.add_argument(
      'image_prefix', help='Location and prefix of image files.',
      metavar='path')
  parser.add_argument(
      '-i', '--include', help='include files whoses name matches this regex',
      metavar='regex')
  parser.add_argument(
      '-e', '--exclude', help='exclude files whose name matches this regex',
      metavar='regex')
  parser.add_argument(
      '-l', '--loglevel', help='log level name', default='warning')
  args = parser.parse_args(argv)

  tool_utils.setup_logging(args.loglevel)

  pairs = collect_glyphstr_file_pairs(
      args.image_prefix, 'svg', include=args.include, exclude=args.exclude)
  add_image_glyphs(args.in_file, args.out_file, pairs)


if __name__ == '__main__':
  main(sys.argv[1:])
