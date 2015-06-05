#!/usr/bin/python

import glob, sys
from fontTools import ttx
from fontTools.ttLib.tables import otTables
from png import PNG

sys.path.append('../../nototools')
from nototools import add_emoji_gsub


def glyph_name(string):
	return "_".join (["u%04X" % ord (char) for char in string])


def add_ligature (font, string):
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
	lig.CompCount = len(string)
	lig.Component = [glyph_name(ch) for ch in string[1:]]
	lig.LigGlyph = glyph_name(string)

	first = glyph_name(string[0])
	try:
		ligatures[first].append(lig)
	except KeyError:
		ligatures[first] = [lig]


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
img_prefix = sys.argv[3]
del sys.argv

font = ttx.TTFont()
font.importXML (in_file)

img_files = {}
glb = "%s*.png" % img_prefix
print "Looking for images matching '%s'." % glb
for img_file in glob.glob (glb):
	codes = img_file[len (img_prefix):-4]
	if "_" in codes:
		pieces = codes.split ("_")
		u = "".join ([unichr (int (code, 16)) for code in pieces])
	else:
		u = unichr (int (codes, 16))
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

for (u, filename) in img_pairs:
	print "Adding glyph for U+%s" % ",".join (["%04X" % ord (char) for char in u])
	n = glyph_name (u)
	g.append (n)
	for char in u:
		if char not in c:
			name = glyph_name (char)
			c[ord (char)] = name
			if len (u) > 1:
				h[name] = [0, 0]
	(img_width, img_height) = PNG (filename).get_size ()
	advance = int (round ((float (ascent+descent) * img_width / img_height)))
	h[n] = [advance, 0]
	if len (u) > 1:
		add_ligature (font, u)

font.saveXML (out_file)
