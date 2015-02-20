#!/usr/bin/python
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

import argparse
import codecs
import os.path
import re
import sys
from xml.parsers import expat
from xml.sax import saxutils

# Expat doesn't allow me to identify empty tags (in particular, with an
# empty tag the parse location for the start and end is not the same) so I
# have to take a dom-like approach if I want to identify them. There are a
# lot of empty tags in svg.  This way I can do some other kinds of cleanup
# as well (remove unnecessary 'g' elements, for instance).

# Use nodes instead of tuples and strings because it's easier to mutate
# a tree of these, and cleaner will want to do this.

class _Elem_Node(object):
  def __init__(self, name, attrs, contents):
    self.name = name
    self.attrs = attrs
    self.contents = contents

  def __repr__(self):
    line = ["elem(name: '%s'" % self.name]
    if self.attrs:
      line.append(" attrs: '%s'" % self.attrs)
    if self.contents:
      line.append(" contents[%s]: '%s'" % (len(self.contents), self.contents))
    line.append(')')
    return ''.join(line)

class _Text_Node(object):
  def __init__(self, text):
    self.text = text

  def __repr__(self):
    return "text('%s')" % self.text

class SvgCleaner(object):
  """Strip out unwanted parts of an svg file, primarily the xml declaration and
  doctype lines, comments, and some attributes of the outermost <svg> element.
  The id will be replaced when it is inserted into the font.  viewBox causes
  unwanted scaling when used in a font and its effect is difficult to
  predict. version is unneeded, xml:space is ignored (we're processing spaces
  so a request to maintain them has no effect).  enable-background appears to
  have no effect.  x and y on the outermost svg element have no effect.  We
  keep width and height, and will elsewhere assume these are the dimensions
  used for the character box."""

  def __init__(self):
    self.reader = SvgCleaner._Reader()
    self.cleaner = SvgCleaner._Cleaner()
    self.writer = SvgCleaner._Writer()

  class _Reader(object):
    """Loosely based on fonttools's XMLReader.  This generates a tree of nodes,
    either element nodes or text nodes.  Successive text content is merged
    into one node, so contents will never contain more than one _Text_Node in
    a row.  This drops comments, xml declarations, and doctypes."""

    def _reset(self, parser):
      self._stack = []
      self._textbuf = []

    def _start_element(self, name, attrs):
      self._flush_textbuf()
      node = _Elem_Node(name, attrs, [])
      if len(self._stack):
        self._stack[-1].contents.append(node)
      self._stack.append(node)

    def _end_element(self, name):
      self._flush_textbuf()
      if len(self._stack) > 1:
        self._stack = self._stack[:-1]

    def _character_data(self, data):
      if len(self._stack):
        self._textbuf.append(data)

    def _flush_textbuf(self):
      if self._textbuf:
        node = _Text_Node(''.join(self._textbuf))
        self._stack[-1].contents.append(node)
        self._textbuf = []

    def from_text(self, data):
      """Return the root node of a tree representing the svg data."""

      parser = expat.ParserCreate()
      parser.StartElementHandler = self._start_element
      parser.EndElementHandler = self._end_element
      parser.CharacterDataHandler = self._character_data
      self._reset(parser)
      parser.Parse(data)
      return self._stack[0]

  class _Cleaner(object):
    def _clean_elem(self, node):
      nattrs = {}
      for k, v in node.attrs.items():
        if node.name == 'svg' and k in ['x', 'y', 'id', 'version', 'viewBox',
                                        'enable-background', 'xml:space']:
          continue
        v = re.sub('\s+', ' ', v)
        nattrs[k] = v
      node.attrs = nattrs

      # scan contents. remove any empty text nodes, or empty 'g' element nodes.
      # if a 'g' element has no attrs and only one subnode, replace it with the
      # subnode.
      wpos = 0
      for n in node.contents:
        if isinstance(n, _Text_Node):
          if not n.text:
            continue
        elif n.name == 'g':
          if not n.contents:
            continue
          if not n.attrs and len(n.contents) == 1:
            n = n.contents[0]
        node.contents[wpos] = n
        wpos += 1
      if wpos < len(node.contents):
        node.contents = node.contents[:wpos]

    def _clean_text(self, node):
      text = node.text.strip()
      # common case is text is empty (line endings between elements)
      if text:
        text = re.sub(r'\s+', ' ', text)
      node.text = text

    def clean(self, node):
      if isinstance(node, _Text_Node):
        self._clean_text(node)
      else:
        # do contents first, so we can check for empty subnodes after
        for n in node.contents:
          self.clean(n)
        self._clean_elem(node)

  class _Writer(object):
    """For text nodes, replaces sequences of whitespace with a single space.
    For elements, replaces sequences of whitespace in attributes, and
    removes unwanted attributes from <svg> elements."""

    def _write_node(self, node, lines, indent):
      """Node is a node generated by _Reader, either a TextNode or an
      ElementNode. Lines is a list to collect the lines of output.  Indent is
      the indentation level for this node."""

      if isinstance(node, _Text_Node):
        if node.text:
          lines.append(node.text)
      else:
        margin = '  ' * indent
        line = [margin]
        line.append('<%s' % node.name)
        for k in sorted(node.attrs.keys()):
          v = node.attrs[k]
          line.append(' %s=%s' % (k, saxutils.quoteattr(v)))
        if node.contents:
          line.append('>')
          lines.append(''.join(line))
          for elem in node.contents:
            self._write_node(elem, lines, indent + 1)
          line = [margin]
          line.append('</%s>' % node.name)
          lines.append(''.join(line))
        else:
          line.append('/>')
          lines.append(''.join(line))

    def to_text(self, root):
      # set up lines for recursive calls, let them append lines, then return
      # the result.
      lines = []
      self._write_node(root, lines, 0)
      return '\n'.join(lines)

  def tree_from_text(self, svg_text):
    return self.reader.from_text(svg_text)

  def clean_tree(self, svg_tree):
    self.cleaner.clean(svg_tree)

  def tree_to_text(self, svg_tree):
    return self.writer.to_text(svg_tree)

  def clean_svg(self, svg_text):
    """Return the cleaned svg_text."""
    tree = self.tree_from_text(svg_text)
    self.clean_tree(tree)
    return self.tree_to_text(tree)


def clean_svg_files(in_dir, out_dir, match_pat=None, quiet=False):
  regex = re.compile(match_pat) if match_pat else None
  count = 0
  if not os.path.isdir(out_dir):
    os.makedirs(out_dir)
    if not quiet:
      print 'created output directory: %s' % out_dir
  cleaner = SvgCleaner()
  for file_name in os.listdir(in_dir):
    if regex and not regex.match(file_name):
      continue
    in_path = os.path.join(in_dir, file_name)
    with open(in_path) as in_fp:
      result = cleaner.clean_svg(in_fp.read())
    out_path = os.path.join(out_dir, file_name)
    with codecs.open(out_path, 'w', 'utf-8') as out_fp:
      if not quiet:
        print 'wrote: %s' % out_path
      out_fp.write(result)
      count += 1
  if not count:
    print 'failed to match any files'
  else:
    print 'processed %s files to %s' % (count, out_dir)


def main():
  parser = argparse.ArgumentParser(
      description="Generate 'cleaned' svg files.")
  parser.add_argument('in_dir', help='Input directory.')
  parser.add_argument('out_dir', help='Output directory.')
  parser.add_argument('regex', help='Regex to select files, default matches all files.', default=None)
  parser.add_argument('--quiet', '-q', help='Quiet operation.', action='store_true')
  args = parser.parse_args()
  clean_svg_files(args.in_dir, args.out_dir, match_pat=args.regex, quiet=args.quiet)


if __name__ == '__main__':
  main()
