#!/usr/bin/env python
#
# Copyright 2013 Google, Inc. All Rights Reserved.
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
# Google Author(s): Behdad Esfahbod, Stuart Gill, Roozbeh Pournader
#


from __future__ import print_function
import sys, struct, StringIO
from png import PNG
import os
from os import path

from nototools import font_data

def get_glyph_name_from_gsub (string, font, cmap_dict):
	ligatures = font['GSUB'].table.LookupList.Lookup[0].SubTable[0].ligatures
	first_glyph = cmap_dict[ord (string[0])]
	rest_of_glyphs = [cmap_dict[ord (ch)] for ch in string[1:]]
	for ligature in ligatures[first_glyph]:
		if ligature.Component == rest_of_glyphs:
			return ligature.LigGlyph


def div (a, b):
	return int (round (a / float (b)))

class FontMetrics:
	def __init__ (self, upem, ascent, descent):
		self.upem = upem
		self.ascent = ascent
		self.descent = descent

class StrikeMetrics:
	def __init__ (self, font_metrics, advance, bitmap_width, bitmap_height):
		self.width = bitmap_width # in pixels
		self.height = bitmap_height # in pixels
		self.advance = advance # in font units
		self.x_ppem = self.y_ppem = div (bitmap_width * font_metrics.upem, advance)

class GlyphMap:
	def __init__ (self, glyph, offset, image_format):
		self.glyph = glyph
		self.offset = offset
		self.image_format = image_format


# Based on http://www.microsoft.com/typography/otspec/ebdt.htm
class CBDT:

	def __init__ (self, font_metrics, options = (), stream = None):
		self.stream = stream if stream != None else bytearray ()
		self.options = options
		self.font_metrics = font_metrics
		self.base_offset = 0
		self.base_offset = self.tell ()

	def tell (self):
		return len (self.stream) - self.base_offset
	def write (self, data):
		self.stream.extend (data)
	def data (self):
		return self.stream

	def write_header (self):
		self.write (struct.pack (">L", 0x00030000)) # FIXED version

	def start_strike (self, strike_metrics):
		self.strike_metrics = strike_metrics
		self.glyph_maps = []

	def write_glyphs (self, glyphs, glyph_filenames, image_format):

		write_func = self.image_write_func (image_format)
		for glyph in glyphs:
			img_file = glyph_filenames[glyph]
                        # print 'writing data for glyph %s' % path.basename(img_file)
			offset = self.tell ()
			write_func (PNG (img_file))
			self.glyph_maps.append (GlyphMap (glyph, offset, image_format))

	def end_strike (self):

		self.glyph_maps.append (GlyphMap (None, self.tell (), None))
		glyph_maps = self.glyph_maps
		del self.glyph_maps
		del self.strike_metrics
		return glyph_maps

	def write_glyphMetrics (self, width, height, big_metrics):

		ascent = self.font_metrics.ascent
		descent = self.font_metrics.descent
		upem = self.font_metrics.upem
		y_ppem = self.strike_metrics.y_ppem

		x_bearing = 0
		# center vertically
		line_height = (ascent + descent) * y_ppem / float (upem)
		line_ascent = ascent * y_ppem / float (upem)
		y_bearing = int (round (line_ascent - .5 * (line_height - height)))
                # fudge y_bearing if calculations are a bit off
                if y_bearing == 128:
                  y_bearing = 127
		advance = width

		vert_x_bearing = - width / 2
		vert_y_bearing = 0
		vert_advance = height

		# print "big glyph metrics h: %d w: %d" % (height, width)
		# smallGlyphMetrics
		# Type	Name
		# BYTE	height
		# BYTE	width
		# CHAR	horiBearingX
		# CHAR	horiBearingY
		# BYTE	horiAdvance
                # add for bigGlyphMetrics:
		# CHAR	vertBearingX
		# CHAR	vertBearingY
		# BYTE	vertAdvance
                try:
                  if big_metrics:
                        self.write (struct.pack ("BBbbBbbB",
					 height, width,
					 x_bearing, y_bearing,
					 advance,
					 vert_x_bearing, vert_y_bearing,
					 vert_advance))
                  else:
                        self.write (struct.pack ("BBbbB",
					 height, width,
					 x_bearing, y_bearing,
					 advance))
                except Exception as e:
                  raise ValueError("%s, h: %d w: %d x: %d y: %d %d a:" % (
                      e, height, width, x_bearing, y_bearing, advance))

	def write_format1 (self, png):

		import cairo
		img = cairo.ImageSurface.create_from_png (png.stream ())
		if img.get_format () != cairo.FORMAT_ARGB32:
			raise Exception ("Expected FORMAT_ARGB32, but image has format %d" % img.get_format ())

		width = img.get_width ()
		height = img.get_height ()
		stride = img.get_stride ()
		data = img.get_data ()

		self.write_smallGlyphMetrics (width, height)

		if sys.byteorder == "little" and stride == width * 4:
			# Sweet.  Data is in desired format, ship it!
			self.write (data)
			return

		# Unexpected stride or endianness, do it the slow way
		offset = 0
		for y in range (height):
			for x in range (width):
				pixel = data[offset + 4 * x: offset + 4 * (x + 1)]
				# Convert to little endian
				pixel = struct.pack ("<I", struct.unpack ("@I", pixel)[0])
				self.write (pixel)
			offset += stride

	png_allowed_chunks =  ["IHDR", "PLTE", "tRNS", "sRGB", "IDAT", "IEND"]

	def write_format17 (self, png):
                self.write_format17or18(png, False)

        def write_format18 (self, png):
                self.write_format17or18(png, True)

	def write_format17or18 (self, png, big_metrics):
		width, height = png.get_size ()

		if 'keep_chunks' not in self.options:
			png = png.filter_chunks (self.png_allowed_chunks)

		self.write_glyphMetrics (width, height, big_metrics)

		png_data = png.data ()
		# ULONG data length
		self.write (struct.pack(">L", len (png_data)))
		self.write (png_data)

	def image_write_func (self, image_format):
		if image_format == 1: return self.write_format1
                if image_format == 17: return self.write_format17
		if image_format == 18: return self.write_format18
		return None


# Based on http://www.microsoft.com/typography/otspec/eblc.htm
class CBLC:

	def __init__ (self, font_metrics, options = (), stream = None):
		self.stream = stream if stream != None else bytearray ()
		self.streams = []
		self.options = options
		self.font_metrics = font_metrics
		self.base_offset = 0
		self.base_offset = self.tell ()

	def tell (self):
		return len (self.stream) - self.base_offset
	def write (self, data):
		self.stream.extend (data)
	def data (self):
		return self.stream
	def push_stream (self, stream):
		self.streams.append (self.stream)
		self.stream = stream
	def pop_stream (self):
		stream = self.stream
		self.stream = self.streams.pop ()
		return stream

	def write_header (self):
		self.write (struct.pack (">L", 0x00030000)) # FIXED version

	def start_strikes (self, num_strikes):
		self.num_strikes = num_strikes
		self.write (struct.pack (">L", self.num_strikes)) # ULONG numSizes
		self.bitmapSizeTables = bytearray ()
		self.otherTables = bytearray ()

	def write_strike (self, strike_metrics, glyph_maps):
		self.strike_metrics = strike_metrics
		self.write_bitmapSizeTable (glyph_maps)
		del self.strike_metrics

	def end_strikes (self):
		self.write (self.bitmapSizeTables)
		self.write (self.otherTables)
		del self.bitmapSizeTables
		del self.otherTables

	def write_sbitLineMetrics_hori (self):

		ascent = self.font_metrics.ascent
		descent = self.font_metrics.descent
		upem = self.font_metrics.upem
		y_ppem = self.strike_metrics.y_ppem

		# sbitLineMetrics
		# Type	Name
		# CHAR	ascender
		# CHAR	descender
		# BYTE	widthMax
		# CHAR	caretSlopeNumerator
		# CHAR	caretSlopeDenominator
		# CHAR	caretOffset
		# CHAR	minOriginSB
		# CHAR	minAdvanceSB
		# CHAR	maxBeforeBL
		# CHAR	minAfterBL
		# CHAR	pad1
		# CHAR	pad2
		line_height = div ((ascent + descent) * y_ppem, upem)
		ascent = div (ascent * y_ppem, upem)
		descent = - (line_height - ascent)
		self.write (struct.pack ("bbBbbbbbbbbb",
					 ascent, descent,
					 self.strike_metrics.width,
					 0, 0, 0,
					 0, 0, 0, 0, # TODO
					 0, 0))

	def write_sbitLineMetrics_vert (self):
		self.write_sbitLineMetrics_hori () # XXX

	def write_indexSubTable1 (self, glyph_maps):

		image_format = glyph_maps[0].image_format

		self.write (struct.pack(">H", 1)) # USHORT indexFormat
		self.write (struct.pack(">H", image_format)) # USHORT imageFormat
		imageDataOffset = glyph_maps[0].offset
		self.write (struct.pack(">L", imageDataOffset)) # ULONG imageDataOffset
		for gmap in glyph_maps[:-1]:
			self.write (struct.pack(">L", gmap.offset - imageDataOffset)) # ULONG offsetArray
			assert gmap.image_format == image_format
		self.write (struct.pack(">L", glyph_maps[-1].offset - imageDataOffset))

	def write_bitmapSizeTable (self, glyph_maps):

		# count number of ranges
		count = 1
		start = glyph_maps[0].glyph
		last_glyph = start
		last_image_format = glyph_maps[0].image_format
		for gmap in glyph_maps[1:-1]:
			if last_glyph + 1 != gmap.glyph or last_image_format != gmap.image_format:
				count += 1
			last_glyph = gmap.glyph
			last_image_format = gmap.image_format
		headersLen = count * 8

		headers = bytearray ()
		subtables = bytearray ()
		start = glyph_maps[0].glyph
		start_id = 0
		last_glyph = start
		last_image_format = glyph_maps[0].image_format
		last_id = 0
		for gmap in glyph_maps[1:-1]:
			if last_glyph + 1 != gmap.glyph or last_image_format != gmap.image_format:
				headers.extend (struct.pack(">HHL", start, last_glyph, headersLen + len (subtables)))
				self.push_stream (subtables)
				self.write_indexSubTable1 (glyph_maps[start_id:last_id+2])
				self.pop_stream ()

				start = gmap.glyph
				start_id = last_id + 1
			last_glyph = gmap.glyph
			last_image_format = gmap.image_format
			last_id += 1
		headers.extend (struct.pack(">HHL", start, last_glyph, headersLen + len (subtables)))
		self.push_stream (subtables)
		self.write_indexSubTable1 (glyph_maps[start_id:last_id+2])
		self.pop_stream ()

		indexTablesSize = len (headers) + len (subtables)
		numberOfIndexSubTables = count
		bitmapSizeTableSize = 48 * self.num_strikes

		indexSubTableArrayOffset = 8 + bitmapSizeTableSize + len (self.otherTables)

		self.push_stream (self.bitmapSizeTables)
		# bitmapSizeTable
		# Type	Name	Description
		# ULONG	indexSubTableArrayOffset	offset to index subtable from beginning of CBLC.
		self.write (struct.pack(">L", indexSubTableArrayOffset))
		# ULONG	indexTablesSize	number of bytes in corresponding index subtables and array
		self.write (struct.pack(">L", indexTablesSize))
		# ULONG	numberOfIndexSubTables	an index subtable for each range or format change
		self.write (struct.pack(">L", numberOfIndexSubTables))
		# ULONG	colorRef	not used; set to 0.
		self.write (struct.pack(">L", 0))
		# sbitLineMetrics	hori	line metrics for text rendered horizontally
		self.write_sbitLineMetrics_hori ()
		self.write_sbitLineMetrics_vert ()
		# sbitLineMetrics	vert	line metrics for text rendered vertically
		# USHORT	startGlyphIndex	lowest glyph index for this size
		self.write (struct.pack(">H", glyph_maps[0].glyph))
		# USHORT	endGlyphIndex	highest glyph index for this size
		self.write (struct.pack(">H", glyph_maps[-2].glyph))
		# BYTE	ppemX	horizontal pixels per Em
		self.write (struct.pack(">B", self.strike_metrics.x_ppem))
		# BYTE	ppemY	vertical pixels per Em
		self.write (struct.pack(">B", self.strike_metrics.y_ppem))
		# BYTE	bitDepth	the Microsoft rasterizer v.1.7 or greater supports the
		#			following bitDepth values, as described below: 1, 2, 4, and 8.
		self.write (struct.pack(">B", 32))
		# CHAR	flags	vertical or horizontal (see bitmapFlags)
		self.write (struct.pack(">b", 0x01))
		self.pop_stream ()

		self.push_stream (self.otherTables)
		self.write (headers)
		self.write (subtables)
		self.pop_stream ()


def main (argv):
	import glob
	from fontTools import ttx, ttLib

	options = []

	option_map = {
		"-V": "verbose",
		"-O": "keep_outlines",
		"-U": "uncompressed",
                "-S": "small_glyph_metrics",
		"-C": "keep_chunks",
	}

	for key, value in option_map.items ():
		if key in argv:
			options.append (value)
			argv.remove (key)

	if len (argv) < 4:
		print("""
Usage:

emoji_builder.py [-V] [-O] [-U] [-S] [-A] font.ttf out-font.ttf strike-prefix...

This will search for files that have strike-prefix followed
by a hex number, and end in ".png".  For example, if strike-prefix
is "icons/uni", then files with names like "icons/uni1f4A9.png" will
be loaded.  All images for the same strike should have the same size
for best results.

If multiple strike-prefix parameters are provided, multiple
strikes will be embedded, in the order provided.

The script then embeds color bitmaps in the font, for characters
that the font already supports, and writes the new font out.

If -V is given, verbose mode is enabled.

If -U is given, uncompressed images are stored (imageFormat=1).

If -S is given, PNG images are stored with small glyph metrics (imageFormat=17).

By default, PNG images are stored with big glyph metrics (imageFormat=18).

If -O is given, the outline tables ('glyf', 'CFF ') and
related tables are NOT dropped from the font.
By default they are dropped.

If -C is given, unused chunks (color profile, etc) are NOT
dropped from the PNG images when embedding.
By default they are dropped.
""", file=sys.stderr)
		sys.exit (1)

	font_file = argv[1]
	out_file = argv[2]
	img_prefixes = argv[3:]
	del argv

	def add_font_table (font, tag, data):
		tab = ttLib.tables.DefaultTable.DefaultTable (tag)
		tab.data = str(data)
		font[tag] = tab

	def drop_outline_tables (font):
		for tag in ['cvt ', 'fpgm', 'glyf', 'loca', 'prep', 'CFF ', 'VORG']:
			try:
				del font[tag]
			except KeyError:
				pass


	print()

	font = ttx.TTFont (font_file)
	print("Loaded font '%s'." % font_file)

	font_metrics = FontMetrics (font['head'].unitsPerEm,
				    font['hhea'].ascent,
				    -font['hhea'].descent)
	print("Font metrics: upem=%d ascent=%d descent=%d." % \
	      (font_metrics.upem, font_metrics.ascent, font_metrics.descent))
	glyph_metrics = font['hmtx'].metrics
	unicode_cmap = font['cmap'].getcmap (3, 10)
	if not unicode_cmap:
		unicode_cmap = font['cmap'].getcmap (3, 1)
	if not unicode_cmap:
		raise Exception ("Failed to find a Unicode cmap.")

	image_format = 1 if 'uncompressed' in options else (17
                if 'small_glyph_metrics' in options else 18)

	ebdt = CBDT (font_metrics, options)
	ebdt.write_header ()
	eblc = CBLC (font_metrics, options)
	eblc.write_header ()
	eblc.start_strikes (len (img_prefixes))

        def is_vs(cp):
                return cp >= 0xfe00 and cp <= 0xfe0f

	for img_prefix in img_prefixes:
		print()

		img_files = {}
		glb = "%s*.png" % img_prefix
		print("Looking for images matching '%s'." % glb)
		for img_file in glob.glob (glb):
			codes = img_file[len (img_prefix):-4]
			if "_" in codes:
				pieces = codes.split ("_")
                                cps = [int(code, 16) for code in pieces]
				uchars = "".join ([unichr(cp) for cp in cps if not is_vs(cp)])
			else:
                                cp = int(codes, 16)
                                if is_vs(cp):
                                        print("ignoring unexpected vs input %04x" % cp)
                                        continue
				uchars = unichr(cp)
			img_files[uchars] = img_file
		if not img_files:
			raise Exception ("No image files found in '%s'." % glb)
		print("Found images for %d characters in '%s'." % (len (img_files), glb))

		glyph_imgs = {}
		advance = width = height = 0
		for uchars, img_file in img_files.items ():
			if len (uchars) == 1:
                                try:
                                        glyph_name = unicode_cmap.cmap[ord (uchars)]
                                except:
                                        print("no cmap entry for %x" % ord(uchars))
                                        raise ValueError("%x" % ord(uchars))
			else:
				glyph_name = get_glyph_name_from_gsub (uchars, font, unicode_cmap.cmap)
			glyph_id = font.getGlyphID (glyph_name)
			glyph_imgs[glyph_id] = img_file
			if "verbose" in options:
				uchars_name = ",".join (["%04X" % ord (char) for char in uchars])
				# print "Matched U+%s: id=%d name=%s image=%s" % (
                                #    uchars_name, glyph_id, glyph_name, img_file)

			advance += glyph_metrics[glyph_name][0]
			w, h = PNG (img_file).get_size ()
			width += w
			height += h

		glyphs = sorted (glyph_imgs.keys ())
		if not glyphs:
			raise Exception ("No common characters found between font and '%s'." % glb)
		print("Embedding images for %d glyphs for this strike." % len (glyphs))

		advance, width, height = (div (x, len (glyphs)) for x in (advance, width, height))
		strike_metrics = StrikeMetrics (font_metrics, advance, width, height)
		print("Strike ppem set to %d." % (strike_metrics.y_ppem))

		ebdt.start_strike (strike_metrics)
		ebdt.write_glyphs (glyphs, glyph_imgs, image_format)
		glyph_maps = ebdt.end_strike ()

		eblc.write_strike (strike_metrics, glyph_maps)

	print()

	ebdt = ebdt.data ()
	add_font_table (font, 'CBDT', ebdt)
	print("CBDT table synthesized: %d bytes." % len (ebdt))
	eblc.end_strikes ()
	eblc = eblc.data ()
	add_font_table (font, 'CBLC', eblc)
	print("CBLC table synthesized: %d bytes." % len (eblc))

	print()

	if 'keep_outlines' not in options:
		drop_outline_tables (font)
		print("Dropped outline ('glyf', 'CFF ') and related tables.")

        # hack removal of cmap pua entry for unknown flag glyph.  If we try to
        # remove it earlier, getGlyphID dies.  Need to restructure all of this
        # code.
        font_data.delete_from_cmap(font, [0xfe82b])

	font.save (out_file)
	print("Output font '%s' generated." % out_file)


if __name__ == '__main__':
	main (sys.argv)
