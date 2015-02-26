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

import math
import random
import re
import string

import svg_cleaner

class SvgBuilder(object):
  """Modifies a font to add SVG glyphs from a document or string.  Once built you
  can call add_from_filename or add_from_doc multiple times to add SVG
  documents, which should contain a single root svg element representing the glyph.
  This element must have width and height attributes (in px), these are used to
  determine how to scale the glyph.  The svg should be designed to fit inside
  this bounds and have its origin at the top left.  Adding the svg generates a
  transform to scale and position the glyph, so the svg element should not have
  a transform attribute since it will be overwritten.  Any id attribute on the
  glyph is also overwritten.

  Adding a glyph can generate additional default glyphs for components of a
  ligature that are not already present.

  It is possible to add SVG images to a font that already has corresponding
  glyphs.  If a glyph exists already, then its hmtx advance is assumed valid.
  Otherwise we will generate an advance based on the image's width and scale
  factor.  Callers should ensure that glyphs for components of ligatures are
  added before the ligatures themselves, otherwise glyphs generated for missing
  ligature components will be assigned zero metrics metrics that will not be
  overridden later."""

  def __init__(self, font_builder):
    font_builder.init_svg()

    self.font_builder = font_builder
    self.cleaner = svg_cleaner.SvgCleaner()

    font = font_builder.font
    self.font_ascent = font['hhea'].ascent
    self.font_height = self.font_ascent - font['hhea'].descent
    self.font_upem = font['head'].unitsPerEm

  def add_from_filename(self, ustr, filename):
    with open(filename, "r") as fp:
      return self.add_from_doc(ustr, fp.read(), filename=filename)

  def _strip_px(self, val):
    return float(val[:-2] if val.endswith('px') else val)

  def add_from_doc(self, ustr, svgdoc, filename=None):
    """Cleans the svg doc, tweaks the root svg element's
    attributes, then updates the font.  ustr is the character or ligature
    string, svgdoc is the svg document xml.  The doc must have a single
    svg root element."""

    # The svg element must have an id attribute of the form 'glyphNNN' where NNN
    # is the glyph id.  We capture the index of the glyph we're adding and write
    # it into the svg.
    #
    # We generate a transform that places the origin at the top left of the
    # ascent and uniformly scales it to fit both the font height (ascent -
    # descent) and glyph advance if it is already present.  The initial viewport
    # is 1000x1000. When present, viewBox scales to fit this and uses default
    # values for preserveAspectRatio that center the viewBox in this viewport
    # ('xMidyMid meet'), and ignores the width and height.  If viewBox is not
    # present, width and height cause a (possibly non-uniform) scale to be
    # applied that map the extent to the viewport.  This is unfortunate for us,
    # since we want to preserve the aspect ratio, and the image is likely
    # designed for a viewport with the width and height it requested.
    #
    # If we have an advance, we want to replicate the behavior of viewBox,
    # except using a 'viewport' of advance, ascent+descent. If we don't have
    # an advance, we scale the height and compute the advance from the scaled
    # width.
    #
    # Lengths using percentage units map 100% to the width/height/diagonal
    # of the viewBox, or if it is not defined, the viewport.  Since we can't
    # define the viewport, we must always have a viewBox.

    cleaner = self.cleaner
    fbuilder = self.font_builder

    tree = cleaner.tree_from_text(svgdoc)

    name, index, exists = fbuilder.add_components_and_ligature(ustr)

    advance = 0
    if exists:
      advance = fbuilder.hmtx[name][0]

    vb = tree.attrs.get('viewBox')
    if vb:
      x, y, w, h = map(self._strip_px, re.split('\s*,\s*|\s+', vb))
    else:
      wid = tree.attrs.get('width')
      ht = tree.attrs.get('height')
      if not (wid and ht):
        raise "missing viewBox and width or height attrs"
      x, y, w, h = 0, 0, self._strip_px(wid), self._strip_px(ht)

    # We're going to assume default values for preserveAspectRatio for now,
    # this preserves aspect ratio and centers in the viewport.
    # First scale to the viewport, which is 1000x1000. compute the scaled
    # extent and translations that center it in the viewport. We won't try
    # to optimize this, it's clearer what we're doing this way.
    if w > h:
        s2vp = 1000.0/w
        sh = s2vp * h
        sty = (1000 - sh) / 2
        sw = 1000.0
        stx = 0.0
    else:
        s2vp = 1000.0/h
        sh = 1000.0
        sty = 0.0
        sw = s2vp * w
        stx = (1000 - sw) / 2

    # now, compute the scale. we scale to the height, unless we have
    # to fit an advance, in which case we scale to the width
    scale = self.font_height / sh
    fit_height = True
    if advance and scale * sw > advance:
      scale = advance / sw
      fit_height = False

    ty = -self.font_ascent - scale * sty
    tx = scale * stx

    if fit_height and advance:
      tx += (advance - scale * sw) / 2
    else:
      ty += (self.font_height - scale * sh) / 2

    cleaner.clean_tree(tree)

    tree.attrs['id'] = 'glyph%s' % index

    transform = 'translate(%g, %g) scale(%g)' % (tx, ty, scale)
    tree.attrs['transform'] = transform

    tree.attrs['viewBox'] = '%g %g %g %g' % (x, y, w, h)

    # In order to clip, we need to create a path and reference it.  You'd think
    # establishing a rectangular clip would be simpler...  Aaaaand... as it
    # turns out, in FF the clip on the outer svg element is only relative to the
    # initial viewport, and is not affected by the viewBox or transform on the
    # svg element.  Unlike chrome. So either we apply an inverse transform, or
    # insert a group with the clip between the svg and its children.  The latter
    # seems cleaner, ultimately.
    clip_id = 'clip_' + ''.join(random.choice(string.ascii_lowercase) for i in range(8))
    clip_text = """<g clip-path="url(#%s)"><clipPath id="%s">
      <path d="M%g %gh%gv%gh%gz"/></clipPath></g>""" % (clip_id, clip_id, x, y, w, h, -w)
    clip_tree = cleaner.tree_from_text(clip_text)
    clip_tree.contents.extend(tree.contents)
    tree.contents = [clip_tree];

    svgdoc = cleaner.tree_to_text(tree)

    hmetrics = None
    if not exists:
      # horiz advance and lsb
      advance = scale * sw
      hmetrics = [int(round(advance)), 0]

    fbuilder.add_svg(svgdoc, hmetrics, name, index)
