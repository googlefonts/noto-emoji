#!/usr/bin/env python

import collections, glob, os, re, sys
from fontTools import ttx
from fontTools.ttLib.tables import otTables
from png import PNG

# PUA character for unknown flag.  This avoids the legacy emoji pua values, but
# is in the same area.
UNKNOWN_FLAG_GLYPH_NAME = "uFE82B"

sys.path.append(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
import add_emoji_gsub


def is_vs(cp):
        return cp >= 0xfe00 and cp <= 0xfe0f

def codes_to_string(codes):
	if "_" in codes:
		pieces = codes.split ("_")
		string = "".join ([unichr (int (code, 16)) for code in pieces])
	else:
          try:
		string = unichr (int (codes, 16))
          except:
            raise ValueError("uh-oh, no unichr for '%s'" % codes)
        return string


def glyph_sequence(string):
        # sequence of names of glyphs that form a ligature
        # variation selectors are stripped
        return ["u%04X" % ord(char) for char in string if not is_vs(ord(char))]


def glyph_name(string):
        # name of a ligature
        # includes variation selectors when present
	return "_".join (["u%04X" % ord (char) for char in string])


def add_ligature (font, seq, name):
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

	ligatures = lookup.SubTable[0].ligatures

	lig = otTables.Ligature()
	lig.CompCount = len(seq)
	lig.Component = seq[1:]
	lig.LigGlyph = name

	first = seq[0]
	try:
		ligatures[first].append(lig)
	except KeyError:
		ligatures[first] = [lig]


# Ligating sequences for emoji that already have a defined codepoint,
# to match the sequences for the related emoji with no codepoint.
# The key is the name of the glyph with the codepoint, the value is the
# name of the sequence in filename form.
EXTRA_SEQUENCES = {
    'u1F46A': '1F468_200D_1F469_200D_1F466', # MWB
    'u1F491': '1F469_200D_2764_FE0F_200D_1F468', # WHM
    'u1F48F': '1F469_200D_2764_FE0F_200D_1F48B_200D_1F468', # WHKM
}

# Flag aliases - from: to
FLAG_ALIASES = {
    'BV': 'NO',
    'CP': 'FR',
    'HM': 'AU',
    'SJ': 'NO',
    'UM': 'US',
}

if len (sys.argv) < 4:
	print >>sys.stderr, """
Usage:

add_glyphs.py font.ttx out-font.ttx strike-prefix...

This will search for files that have strike-prefix followed by one or more
hex numbers (separated by underscore if more than one), and end in ".png".
For example, if strike-prefix is "icons/u", then files with names like
"icons/u1F4A9.png" or "icons/u1F1EF_1F1F5.png" will be loaded.  The script
then adds cmap, htmx, and potentially GSUB entries for the Unicode
characters found.  The advance width will be chosen based on image aspect
ratio.  If Unicode values outside the BMP are desired, the existing cmap
table should be of the appropriate (format 12) type.  Only the first cmap
table and the first GSUB lookup (if existing) are modified.
"""
	sys.exit (1)

in_file = sys.argv[1]
out_file = sys.argv[2]
img_prefixen = sys.argv[3:]
del sys.argv

font = ttx.TTFont()
font.importXML (in_file)

img_files = {}
for img_prefix in img_prefixen:
        glb = "%s*.png" % img_prefix
        print "Looking for images matching '%s'." % glb
        for img_file in glob.glob (glb):
        	codes = img_file[len (img_prefix):-4]
                u = codes_to_string(codes)
                if u in img_files:
                        print 'overwriting %s with %s' % (img_files[u], img_file)
        	img_files[u] = img_file
if not img_files:
	raise Exception ("No image files found in '%s'." % glb)

ascent = font['hhea'].ascent
descent = -font['hhea'].descent

g = font['GlyphOrder'].glyphOrder
c = font['cmap'].tables[0].cmap
h = font['hmtx'].metrics

# Sort the characters by length, then codepoint, to keep the order stable
# and avoid adding empty glyphs for multi-character glyphs if any piece is
# also included.
img_pairs = img_files.items ()
img_pairs.sort (key=lambda pair: (len (pair[0]), pair[0]))

glyph_names = set()
ligatures = {}

def add_lig_sequence(ligatures, seq, n):
        # Assume sequences with ZWJ are emoji 'ligatures' and rtl order
        # is also valid.  Internal permutations, though, no.
        # We associate a sequence with a filename.  We can overwrite the
        # sequence with a different filename later.
        tseq = tuple(seq)
        if tseq in ligatures:
                print 'lig sequence %s, replace %s with %s' % (
                    tseq, ligatures[tseq], n)
        ligatures[tseq] = n
        if 'u200D' in seq:
                rev_seq = seq[:]
                rev_seq.reverse()
                trseq = tuple(rev_seq)
                # if trseq in ligatures:
                #        print 'rev lig sequence %s, replace %s with %s' % (
                #        trseq, ligatures[trseq], n)
                ligatures[trseq] = n


for (u, filename) in img_pairs:
	n = glyph_name (u)
        glyph_names.add(n)
	# print "Adding glyph for %s" % n

	g.append (n)
	for char in u:
                cp = ord(char)
		if cp not in c and not is_vs(cp):
			name = glyph_name (char)
			c[cp] = name
			if len (u) > 1:
				h[name] = [0, 0]
	(img_width, img_height) = PNG (filename).get_size ()
	advance = int (round ((float (ascent+descent) * img_width / img_height)))
	h[n] = [advance, 0]
	if len (u) > 1:
                seq = glyph_sequence(u)
                add_lig_sequence(ligatures, seq, n)

for n in EXTRA_SEQUENCES:
        if n in glyph_names:
                seq = glyph_sequence(codes_to_string(EXTRA_SEQUENCES[n]))
                add_lig_sequence(ligatures, seq, n)
        else:
                print 'extras: no glyph for %s' % n

# Add missing regional indicator sequences and flag aliases
# if we support any.
regional_names = frozenset('u%X' % cp for cp in range(0x1F1E6, 0x1F200))

def _is_flag_sequence(t):
  return len(t) == 2 and t[0] in regional_names and t[1] in regional_names

have_flags = False
for k in ligatures:
  if _is_flag_sequence(k):
    have_flags = True
    break

if have_flags and UNKNOWN_FLAG_GLYPH_NAME not in glyph_names:
  raise ValueError(
      'Have flags but no unknown flag glyph "%s"' % UNKNOWN_FLAG_GLYPH_NAME)

# sigh, too many separate files with the same code.
# copied from add_emoji_gsub.
def _reg_indicator(letter):
  assert 'A' <= letter <= 'Z'
  return 0x1F1E6 + ord(letter) - ord('A')

def _reg_lig_sequence(flag_name):
  """Returns a tuple of strings naming the codepoints that form the ligature."""
  assert len(flag_name) == 2
  return tuple('u%X' % _reg_indicator(cp) for cp in flag_name)

def _reg_lig_name(flag_name):
  """Returns a glyph name for the flag name."""
  return '_'.join(_reg_lig_sequence(flag_name))

if have_flags:
  print 'Adding flag aliases.'
  for flag_from, flag_to in FLAG_ALIASES.iteritems():
    seq = _reg_lig_sequence(flag_from)
    name = _reg_lig_name(flag_to)
    add_lig_sequence(ligatures, seq, name)

  print 'Adding unused flag sequences'
  # every flag sequence we don't have gets the missing flag glyph
  for first in regional_names:
    for second in regional_names:
      seq = (first, second)
      if seq not in ligatures:
        add_lig_sequence(ligatures, seq, UNKNOWN_FLAG_GLYPH_NAME)


keyed_ligatures = collections.defaultdict(list)
for k, v in ligatures.iteritems():
        first = k[0]
        keyed_ligatures[first].append((k, v))

for base in sorted(keyed_ligatures):
        pairs = keyed_ligatures[base]
        # print 'base %s has %d sequences' % (base, len(pairs))

        # Sort longest first, this ensures longer sequences with common prefixes
        # are handled before shorter ones.  It would be better to have multiple
        # lookups, most likely.
        pairs.sort(key = lambda pair: (len(pair[0]), pair[0]), reverse=True)
        for seq, name in pairs:
                # print seq, name
                add_ligature(font, seq, name)

font.saveXML (out_file)
