#!/usr/bin/env python
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

from __future__ import print_function
import argparse
import os
import os.path
import re
import sys

from fontTools import ttx

import add_svg_glyphs

def do_generate_test_html(font_basename, pairs, glyph=None, verbosity=1):
  header = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style type="text/css">
@font-face { font-family: svgfont; src: url("%s") }
body { font-family: sans-serif; font-size: 24px }
#emoji span { font-family: svgfont, sans-serif }
#panel { font-family: svgfont, sans-serif; font-size: 256px }
#paneltitle { font-family: sans-serif; font-size: 36px }
</style>
<script type="text/javascript">
function hexify(text) {
  var surr_offset = 0x10000 - (0xd800 << 10) - 0xdc00
  var str = text.trim()
  var len = str.length
  var result = ""
  for (var i = 0; i < len; ++i) {
    var cp = str.charCodeAt(i)
    if (cp >= 0xd800 && cp < 0xdc00 && i < len - 1) {
      ncp = str.charCodeAt(i+1)
      if (ncp >= 0xdc00 && ncp < 0xe000) {
        cp = (cp << 10) + ncp + surr_offset
        ++i;
      }
    }
    result += " 0x" + cp.toString(16)
  }
  return result
};

function showText(event) {
  var text = event.target.textContent
  var p = document.getElementById('panel')
  p.textContent = text
  p = document.getElementById('paneltitle')
  p.textContent = hexify(text)
};

function setup() {
  var t = document.getElementById('emoji')
  var tdlist = t.getElementsByTagName('span')
  for (var i = 0; i < tdlist.length; ++i) {
    var e = tdlist[i]
    e.onmouseover = showText
  }
};
</script>
</head>"""

  body_head = r"""<body onload="setup();">
<p>Test for SVG glyphs in %(font)s.  It uses the proposed
<a href="http://lists.w3.org/Archives/Public/public-svgopentype/2013Jul/0003.html">SVG-in-OpenType format</a>.
View using Firefox&nbsp;26 and later.
<div style="float:left; text-align:center; margin:0 10px; width:40%%">
<div id='panel' style="margin-left:auto; margin-right:auto">%(glyph)s</div>
<div id='paneltitle' style="margin-left:auto; margin-right:auto">%(glyph_hex)s</div>
</div>
<div id='emoji'><p>"""

  body_tail = r"""</div>
</body>
</html>
"""

  font_name = font_basename + ".woff"
  html_name = font_basename + "_test.html"

  found_initial_glyph = False
  initial_glyph_str = None;
  initial_glyph_hex = None;
  text_parts = []
  for glyphstr, _ in pairs:
    name_parts = []
    hex_parts = []
    for cp in glyphstr:
      hex_str = hex(ord(cp))
      name_parts.append('&#x%s;' % hex_str[2:])
      hex_parts.append(hex_str)
    glyph_str = ''.join(name_parts)

    if not found_initial_glyph:
      if not glyph or glyph_str == glyph:
        initial_glyph_str = glyph_str
        initial_glyph_hex = ' '.join(hex_parts)
        found_initial_glyph = True
      elif not initial_glyph_str:
        initial_glyph_str = glyph_str
        initial_glyph_hex = ' '.join(hex_parts)

    text = '<span>%s</span>' % glyph_str
    text_parts.append(text)

  if verbosity and glyph and not found_initial_glyph:
    print("Did not find glyph '%s', using initial glyph '%s'" % (glyph, initial_glyph_str))
  elif verbosity > 1 and not glyph:
    print("Using initial glyph '%s'" % initial_glyph_str)

  lines = [header % font_name]
  lines.append(body_head % {'font':font_name, 'glyph':initial_glyph_str,
                            'glyph_hex':initial_glyph_hex})
  lines.extend(text_parts) # we'll end up with space between each emoji
  lines.append(body_tail)
  output = '\n'.join(lines)
  with open(html_name, 'w') as fp:
    fp.write(output)
  if verbosity:
    print('Wrote ' + html_name)


def do_generate_fonts(template_file, font_basename, pairs, reuse=0, verbosity=1):
  out_woff = font_basename + '.woff'
  if reuse > 1 and os.path.isfile(out_woff) and os.access(out_woff, os.R_OK):
    if verbosity:
      print('Reusing ' + out_woff)
    return

  out_ttx = font_basename + '.ttx'
  if reuse == 0:
    add_svg_glyphs.add_image_glyphs(template_file, out_ttx, pairs, verbosity=verbosity)
  elif verbosity:
    print('Reusing ' + out_ttx)

  quiet=verbosity < 2
  font = ttx.TTFont(flavor='woff', quiet=quiet)
  font.importXML(out_ttx, quiet=quiet)
  font.save(out_woff)
  if verbosity:
    print('Wrote ' + out_woff)


def main(argv):
  usage = """This will search for files that have image_prefix followed by one or more
      hex numbers (separated by underscore if more than one), and end in ".svg".
      For example, if image_prefix is "icons/u", then files with names like
      "icons/u1F4A9.svg" or "icons/u1F1EF_1F1F5.svg" will be found. It generates
      an SVG font from this, converts it to woff, and also generates an html test
      page containing text for all the SVG glyphs."""

  parser = argparse.ArgumentParser(
      description='Generate font and html test file.', epilog=usage)
  parser.add_argument('template_file', help='name of template .ttx file')
  parser.add_argument('image_prefix', help='location and prefix of image files')
  parser.add_argument('-i', '--include', help='include files whoses name matches this regex')
  parser.add_argument('-e', '--exclude', help='exclude files whose name matches this regex')
  parser.add_argument('-o', '--out_basename', help='base name of (ttx, woff, html) files to generate, '
                      'defaults to the template base name')
  parser.add_argument('-g', '--glyph', help='set the initial glyph text (html encoded string), '
                      'defaults to first glyph')
  parser.add_argument('-rt', '--reuse_ttx_font', dest='reuse_font', help='use existing ttx font',
                      default=0, const=1, action='store_const')
  parser.add_argument('-r', '--reuse_font', dest='reuse_font', help='use existing woff font',
                      const=2, action='store_const')
  parser.add_argument('-q', '--quiet', dest='v', help='quiet operation', default=1,
                      action='store_const', const=0)
  parser.add_argument('-v', '--verbose', dest='v', help='verbose operation',
                      action='store_const', const=2)
  args = parser.parse_args(argv)

  pairs = add_svg_glyphs.collect_glyphstr_file_pairs(
    args.image_prefix, 'svg', include=args.include, exclude=args.exclude, verbosity=args.v)
  add_svg_glyphs.sort_glyphstr_tuples(pairs)

  out_basename = args.out_basename
  if not out_basename:
    out_basename = args.template_file.split('.')[0] # exclude e.g. '.tmpl.ttx'
    if args.v:
      print("Output basename is %s." % out_basename)
  do_generate_fonts(args.template_file, out_basename, pairs, reuse=args.reuse_font, verbosity=args.v)
  do_generate_test_html(out_basename, pairs, glyph=args.glyph, verbosity=args.v)

if __name__ == '__main__':
  main(sys.argv[1:])
