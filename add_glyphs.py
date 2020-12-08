#!/usr/bin/env python3

"""Extend a ttx file with additional data.

Takes a ttx file and one or more directories containing image files named
after sequences of codepoints, extends the cmap, hmtx, GSUB, and GlyphOrder
tables in the source ttx file based on these sequences, and writes out a new
ttx file.

This can also apply aliases from an alias file."""

import argparse
import collections
import os
from os import path
import re
import sys

from fontTools import ttx
from fontTools.ttLib.tables import otTables
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
from fontTools.ttLib import newTable

import add_emoji_gsub
import add_aliases

sys.path.append(
    path.join(os.path.dirname(__file__), 'third_party', 'color_emoji'))
from png import PNG


def get_seq_to_file(image_dir, prefix, suffix):
  """Return a mapping from codepoint sequences to files in the given directory,
  for files that match the prefix and suffix.  File names with this prefix and
  suffix should consist of codepoints in hex separated by underscore.  'fe0f'
  (the codepoint of the emoji presentation variation selector) is stripped from
  the sequence.
  """
  start = len(prefix)
  limit = -len(suffix)
  seq_to_file = {}
  for name in os.listdir(image_dir):
    if not (name.startswith(prefix) and name.endswith(suffix)):
      continue
    try:
      cps = [int(s, 16) for s in name[start:limit].split('_')]
      seq = tuple(cp for cp in cps if cp != 0xfe0f)
    except:
      raise Exception('could not parse "%s"' % name)
    for cp in cps:
      if not (0 <= cp <= 0x10ffff):
        raise Exception('bad codepoint(s) in "%s"' % name)
    if seq in seq_to_file:
      raise Exception('duplicate sequence for "%s" in %s' % (name, image_dir))
    seq_to_file[seq] = path.join(image_dir, name)
  return seq_to_file


def collect_seq_to_file(image_dirs, prefix, suffix):
  """Return a sequence to file mapping by calling get_seq_to_file on a list
  of directories.  When sequences for files in later directories match those
  from earlier directories, the later file replaces the earlier one.
  """
  seq_to_file = {}
  for image_dir in image_dirs:
    seq_to_file.update(get_seq_to_file(image_dir, prefix, suffix))
  return seq_to_file


def remap_values(seq_to_file, map_fn):
  return {k: map_fn(v) for k, v in seq_to_file.items()}


def get_png_file_to_advance_mapper(lineheight):
  def map_fn(filename):
    wid, ht = PNG(filename).get_size()
    return int(round(float(lineheight) * wid / ht))
  return map_fn


def cp_name(cp):
  """return uniXXXX or uXXXXX(X) as a name for the glyph mapped to this cp."""
  return '%s%04X' % ('u' if cp > 0xffff else 'uni', cp)


def seq_name(seq):
  """Sequences of length one get the cp_name.  Others start with 'u' followed by
  two or more 4-to-6-digit hex strings separated by underscore."""
  if len(seq) == 1:
    return cp_name(seq[0])
  return 'u' + '_'.join('%04X' % cp for cp in seq)


def collect_cps(seqs):
  cps = set()
  for seq in seqs:
    cps.update(seq)
  return cps


def get_glyphorder_cps_and_truncate(glyphOrder):
  """This scans glyphOrder for names that correspond to a single codepoint
  using the 'u(ni)XXXXXX' syntax.  All names that don't match are moved
  to the front the glyphOrder list in their original order, and the
  list is truncated.  The ones that do match are returned as a set of
  codepoints."""
  glyph_name_re = re.compile(r'^u(?:ni)?([0-9a-fA-F]{4,6})$')
  cps = set()
  write_ix = 0
  for ix, name in enumerate(glyphOrder):
    m = glyph_name_re.match(name)
    if m:
      cps.add(int(m.group(1), 16))
    else:
      glyphOrder[write_ix] = name
      write_ix += 1
  del glyphOrder[write_ix:]
  return cps


def get_all_seqs(font, seq_to_advance):
  """Copies the sequences from seq_to_advance and extends it with single-
  codepoint sequences from the GlyphOrder table as well as those internal
  to sequences in seq_to_advance.  Reduces the GlyphOrder table. """

  all_seqs = set(seq_to_advance.keys())
  # using collect_cps includes cps internal to a seq
  cps = collect_cps(all_seqs)
  glyphOrder = font.getGlyphOrder()
  # extract cps in glyphOrder and reduce glyphOrder to only those that remain
  glyphOrder_cps = get_glyphorder_cps_and_truncate(glyphOrder)
  cps.update(glyphOrder_cps)
  # add new single codepoint sequences from glyphOrder and sequences
  all_seqs.update((cp,) for cp in cps)
  return all_seqs


def get_font_cmap(font):
  """Return the first cmap in the font, we assume it exists and is a unicode
  cmap."""
  return font['cmap'].tables[0].cmap


def add_glyph_data(font, seqs, seq_to_advance, vadvance, add_glyf):
  """Add hmtx and GlyphOrder data for all sequences in seqs, and ensures there's
  a cmap entry for each single-codepoint sequence.  Seqs not in seq_to_advance
  will get a zero advance."""

  # We allow the template cmap to omit mappings for single-codepoint glyphs
  # defined in the template's GlyphOrder table.  Similarly, the hmtx table can
  # omit advances.  We assume glyphs named 'uniXXXX' or 'uXXXXX(X)' in the
  # GlyphOrder table correspond to codepoints based on the name; we don't
  # attempt to handle other types of names and these must occur in the cmap and
  # hmtx tables in the template.
  #
  # seq_to_advance maps sequences (including single codepoints) to advances.
  # All codepoints in these sequences will be added to the cmap.  Some cps
  # in these sequences have no corresponding single-codepoint sequence, they
  # will also get added.
  #
  # The added codepoints have no advance information, so will get a zero
  # advance.

  cmap = get_font_cmap(font)
  hmtx = font['hmtx'].metrics
  vmtx = font['vmtx'].metrics

  # Add glyf table so empty glyphs will be added to ensure compatibility
  # with systems requiring a glyf table, like Windows 10.
  if add_glyf:
    pen = TTGlyphPen(None)
    empty_glyph = pen.glyph()
    font['loca'] = newTable("loca")
    font['glyf'] = glyf_table = newTable("glyf")
    glyf_table.glyphOrder = font.getGlyphOrder()
    glyf_table.glyphs = {g: empty_glyph for g in glyf_table.glyphOrder}

  # We don't expect sequences to be in the glyphOrder, since we removed all the
  # single-cp sequences from it and don't expect it to already contain names
  # corresponding to multiple-cp sequencess.  But just in case, we use
  # reverseGlyphMap to avoid duplicating names accidentally.

  updatedGlyphOrder = False
  reverseGlyphMap = font.getReverseGlyphMap()

  # Order the glyphs by grouping all the single-codepoint sequences first,
  # then order by sequence so that related sequences are together.  We group
  # by single-codepoint sequence first in order to keep these glyphs together--
  # they're used in the coverage tables for some of the substitutions, and
  # those tables can be more compact this way.
  for seq in sorted(seqs, key=lambda s: (0 if len(s) == 1 else 1, s)):
    name = seq_name(seq)
    if len(seq) == 1:
      cmap[seq[0]] = name
    advance = seq_to_advance.get(seq, 0)
    hmtx[name] = [advance, 0]
    vmtx[name] = [vadvance, 0]
    if name not in reverseGlyphMap:
      font.glyphOrder.append(name)
      updatedGlyphOrder=True
    if add_glyf:
      glyf_table[name] = empty_glyph

  if updatedGlyphOrder:
    delattr(font, '_reverseGlyphOrderDict')

def add_aliases_to_cmap(font, aliases):
  """Some aliases might map a single codepoint to some other sequence.  These
  should map directly to the glyph for that sequence in the cmap.  (Others will
  map via GSUB).
  """
  if not aliases:
    return

  cp_aliases = [seq for seq in aliases if len(seq) == 1]
  if not cp_aliases:
    return

  cmap = get_font_cmap(font)
  for src_seq in cp_aliases:
    cp = src_seq[0]
    name = seq_name(aliases[src_seq])
    cmap[cp] = name


def get_rtl_seq(seq):
  """Return the rtl variant of the sequence, if it has one, else the empty
  sequence.
  """
  # Sequences with ZWJ in them will reflect.  Fitzpatrick modifiers
  # however do not, so if we reflect we make a pass to swap them back into their
  # logical order.
  # Used to check for TAG_END 0xe007f as well but Android fontchain_lint
  # dislikes the resulting mangling of flags for England, Scotland, Wales.

  ZWJ = 0x200d
  def is_fitzpatrick(cp):
    return 0x1f3fb <= cp <= 0x1f3ff

  if ZWJ not in seq:
    return ()

  rev_seq = list(seq)
  rev_seq.reverse()
  for i in range(1, len(rev_seq)):
    if is_fitzpatrick(rev_seq[i-1]):
      tmp = rev_seq[i]
      rev_seq[i] = rev_seq[i-1]
      rev_seq[i-1] = tmp
  return tuple(rev_seq)


def get_gsub_ligature_lookup(font):
  """If the font does not have a GSUB table, create one with a ligature
  substitution lookup.  If it does, ensure the first lookup is a properly
  initialized ligature substitution lookup.  Return the lookup."""

  # The template might include more lookups after lookup 0, if it has a
  # GSUB table.
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
    assert lookup.LookupFlag == 0

    # importXML doesn't fully init GSUB structures, so help it out
    st = lookup.SubTable[0]
    if not hasattr(lookup, 'LookupType'):
      assert st.LookupType == 4
      setattr(lookup, 'LookupType', 4)

    if not hasattr(st, 'ligatures'):
      setattr(st, 'ligatures', {})

  return lookup


def add_ligature_sequences(font, seqs, aliases):
  """Add ligature sequences."""

  seq_to_target_name = {
      seq: seq_name(seq) for seq in seqs if len(seq) > 1}
  if aliases:
    seq_to_target_name.update({
        seq: seq_name(aliases[seq]) for seq in aliases if len(seq) > 1})
  if not seq_to_target_name:
    return

  rtl_seq_to_target_name = {
      get_rtl_seq(seq): name for seq, name in seq_to_target_name.items()}
  seq_to_target_name.update(rtl_seq_to_target_name)
  # sequences that don't have rtl variants get mapped to the empty sequence,
  # delete it.
  if () in seq_to_target_name:
    del seq_to_target_name[()]

  # organize by first codepoint in sequence
  keyed_ligatures = collections.defaultdict(list)
  for t in seq_to_target_name.items():
    first_cp = t[0][0]
    keyed_ligatures[first_cp].append(t)

  def add_ligature(lookup, cmap, seq, name):
    # The sequences consist of codepoints, but the entries in the ligature table
    # are glyph names.  Aliasing can give single codepoints names based on
    # sequences (e.g. 'guardsman' with 'male guardsman') so we map the
    # codepoints through the cmap to get the glyph names.
    glyph_names = [cmap[cp] for cp in seq]

    lig = otTables.Ligature()
    lig.CompCount = len(seq)
    lig.Component = glyph_names[1:]
    lig.LigGlyph = name

    ligatures = lookup.SubTable[0].ligatures
    first_name = glyph_names[0]
    try:
      ligatures[first_name].append(lig)
    except KeyError:
      ligatures[first_name] = [lig]

  lookup = get_gsub_ligature_lookup(font)
  cmap = get_font_cmap(font)
  for first_cp in sorted(keyed_ligatures):
    pairs = keyed_ligatures[first_cp]

    # Sort longest first, this ensures longer sequences with common prefixes
    # are handled before shorter ones.  The secondary sort is a standard
    # sort on the codepoints in the sequence.
    pairs.sort(key = lambda pair: (-len(pair[0]), pair[0]))
    for seq, name in pairs:
      add_ligature(lookup, cmap, seq, name)

def add_cmap_format_4(font):
  """Add cmap format 4 table for Windows support, based on the
  format 12 cmap."""

  cmap = get_font_cmap(font)

  newtable = CmapSubtable.newSubtable(4)
  newtable.platformID = 3
  newtable.platEncID = 1
  newtable.language = 0

  # Format 4 only has unicode values 0x0000 to 0xFFFF
  newtable.cmap = {cp: name for cp, name in cmap.items() if cp <= 0xFFFF}

  font['cmap'].tables.append(newtable)

def update_font_data(font, seq_to_advance, vadvance, aliases, add_cmap4, add_glyf):
  """Update the font's cmap, hmtx, GSUB, and GlyphOrder tables."""
  seqs = get_all_seqs(font, seq_to_advance)
  add_glyph_data(font, seqs, seq_to_advance, vadvance, add_glyf)
  add_aliases_to_cmap(font, aliases)
  add_ligature_sequences(font, seqs, aliases)
  if add_cmap4:
    add_cmap_format_4(font)

def apply_aliases(seq_dict, aliases):
  """Aliases is a mapping from sequence to replacement sequence.  We can use
  an alias if the target is a key in the dictionary.  Furthermore, if the
  source is a key in the dictionary, we can delete it.  This updates the
  dictionary and returns the usable aliases."""
  usable_aliases = {}
  for k, v in aliases.items():
    if v in seq_dict:
      usable_aliases[k] = v
      if k in seq_dict:
        del seq_dict[k]
  return usable_aliases


def update_ttx(in_file, out_file, image_dirs, prefix, ext, aliases_file, add_cmap4, add_glyf):
  if ext != '.png':
    raise Exception('extension "%s" not supported' % ext)

  seq_to_file = collect_seq_to_file(image_dirs, prefix, ext)
  if not seq_to_file:
    raise ValueError(
        'no sequences with prefix "%s" and extension "%s" in %s' % (
            prefix, ext, ', '.join(image_dirs)))

  aliases = None
  if aliases_file:
    aliases = add_aliases.read_emoji_aliases(aliases_file)
    aliases = apply_aliases(seq_to_file, aliases)

  font = ttx.TTFont()
  font.importXML(in_file)

  lineheight = font['hhea'].ascent - font['hhea'].descent
  map_fn = get_png_file_to_advance_mapper(lineheight)
  seq_to_advance = remap_values(seq_to_file, map_fn)

  vadvance = font['vhea'].advanceHeightMax if 'vhea' in font else lineheight

  update_font_data(font, seq_to_advance, vadvance, aliases, add_cmap4, add_glyf)

  font.saveXML(out_file)


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '-f', '--in_file', help='ttx input file', metavar='file', required=True)
  parser.add_argument(
      '-o', '--out_file', help='ttx output file', metavar='file', required=True)
  parser.add_argument(
      '-d', '--image_dirs', help='directories containing image files',
      nargs='+', metavar='dir', required=True)
  parser.add_argument(
      '-p', '--prefix', help='file prefix (default "emoji_u")',
      metavar='pfx', default='emoji_u')
  parser.add_argument(
      '-e', '--ext', help='file extension (default ".png", currently only '
      '".png" is supported',  metavar='ext', default='.png')
  parser.add_argument(
      '-a', '--aliases', help='process alias table', const='emoji_aliases.txt',
      nargs='?', metavar='file')
  parser.add_argument(
      '--add_cmap4', help='add cmap format 4 table', dest='add_cmap4', action='store_true')
  parser.add_argument(
      '--add_glyf', help='add glyf and loca tables', dest='add_glyf', action='store_true')
  args = parser.parse_args()

  update_ttx(
      args.in_file, args.out_file, args.image_dirs, args.prefix, args.ext,
      args.aliases, args.add_cmap4, args.add_glyf)


if __name__ == '__main__':
  main()
