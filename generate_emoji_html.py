#!/usr/bin/env python3
#
# Copyright 2016 Google Inc. All rights reserved.
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

"""Build an html page showing emoji images.

This takes a list of directories containing emoji image files, and
builds an html page presenting the images along with their composition
(for sequences) and unicode names (for individual emoji)."""
from __future__ import print_function

import argparse
import codecs
import collections
import datetime
import glob
import os
from os import path
import re
import shutil
import string
import sys

from nototools import tool_utils
from nototools import unicode_data

import add_aliases

_default_dir = 'png/128'
_default_ext = 'png'
_default_prefix = 'emoji_u'
_default_title = 'Emoji List'

# DirInfo represents information about a directory of file names.
# - directory is the directory path
# - title is the title to use for this directory
# - filemap is a dict mapping from a tuple of codepoints to the name of
#   a file in the directory.
DirInfo = collections.namedtuple('DirInfo', 'directory, title, filemap')


def _merge_keys(dicts):
  """Return the union of the keys in the list of dicts."""
  keys = []
  for d in dicts:
    keys.extend(d.keys())
  return frozenset(keys)


def _generate_row_cells(
    key, font, aliases, excluded, dir_infos, basepaths, colors):
  CELL_PREFIX = '<td>'
  indices = range(len(basepaths))
  def _cell(info, basepath):
    if key in info.filemap:
      return '<img src="%s">' % path.join(basepath, info.filemap[key])
    if key in aliases:
      return 'alias'
    if key in excluded:
      return 'exclude'
    return 'missing'

  def _text_cell(text_dir):
    text = ''.join(chr(cp) for cp in key)
    return '<span class="efont" dir="%s">%s</span>' % (text_dir, text)

  if font:
    row_cells = [
        CELL_PREFIX + _text_cell(text_dir)
        for text_dir in ('ltr', 'rtl')]
  else:
    row_cells = []
  row_cells.extend(
      [CELL_PREFIX + _cell(dir_infos[i], basepaths[i])
       for i in indices])
  if len(colors) > 1:
    ix = indices[-1]
    extension = CELL_PREFIX + _cell(dir_infos[ix], basepaths[ix])
    row_cells.extend([extension] * (len(colors) - 1))
  return row_cells


def _get_desc(key_tuple, aliases, dir_infos, basepaths):
  CELL_PREFIX = '<td>'
  def _get_filepath(cp):
    def get_key_filepath(key):
      for i in range(len(dir_infos)):
        info = dir_infos[i]
        if key in info.filemap:
          basepath = basepaths[i]
          return path.join(basepath, info.filemap[key])
      return None

    cp_key = tuple([cp])
    cp_key = unicode_data.get_canonical_emoji_sequence(cp_key) or cp_key
    fp = get_key_filepath(cp_key)
    if not fp:
      if cp_key in aliases:
        fp = get_key_filepath(aliases[cp_key])
      else:
        print('no alias for %s' % unicode_data.seq_to_string(cp_key))
    if not fp:
      print('no part for %s in %s' % (
          unicode_data.seq_to_string(cp_key),
          unicode_data.seq_to_string(key_tuple)))
    return fp

  def _get_part(cp):
    if cp == 0x200d:  # zwj, common so replace with '+'
      return '+'
    if unicode_data.is_regional_indicator(cp):
      return unicode_data.regional_indicator_to_ascii(cp)
    if unicode_data.is_tag(cp):
      return unicode_data.tag_character_to_ascii(cp)
    fname = _get_filepath(cp)
    if fname:
      return '<img src="%s">' % fname
    raise Exception()

  if len(key_tuple) == 1:
    desc = '%04x' % key_tuple
  else:
    desc = ' '.join('%04x' % cp for cp in key_tuple)
    if len(unicode_data.strip_emoji_vs(key_tuple)) > 1:
      try:
        desc += ' (%s)' % ''.join(
            _get_part(cp) for cp in key_tuple if cp != 0xfe0f)
      except:
        pass
  return CELL_PREFIX + desc


def _get_name(key_tuple, annotations):
  annotation = None if annotations is None else annotations.get(key_tuple)
  CELL_PREFIX = '<td%s>' % (
      '' if annotation is None else ' class="%s"' % annotation)

  seq_name = unicode_data.get_emoji_sequence_name(key_tuple)
  if seq_name == None:
    if key_tuple == (0x20e3,):
      seq_name = '(combining enlosing keycap)'
    elif key_tuple == (0xfe82b,):
      seq_name = '(unknown flag PUA codepoint)'
    else:
      print('no name for %s' % unicode_data.seq_to_string(key_tuple))
      seq_name = '(oops)'
  return CELL_PREFIX + seq_name


def _collect_aux_info(dir_infos, keys):
  """Returns a map from dir_info_index to a set of keys of additional images
  that we will take from the directory at that index."""

  target_key_to_info_index = {}
  for key in keys:
    if len(key) == 1:
      continue
    for cp in key:
      target_key = tuple([cp])
      if target_key in keys or target_key in target_key_to_info_index:
        continue
      for i, info in enumerate(dir_infos):
        if target_key in info.filemap:
          target_key_to_info_index[target_key] = i
          break
      if target_key not in target_key_to_info_index:
        # we shouldn't try to use it in the description.  maybe report this?
        pass

  # now we need to invert the map
  aux_info = collections.defaultdict(set)
  for key, index in target_key_to_info_index.items():
    aux_info[index].add(key)

  return aux_info


def _generate_content(
    basedir, font, dir_infos, keys, aliases, excluded, annotations, standalone,
    colors):
  """Generate an html table for the infos.  Basedir is the parent directory of
  the content, filenames will be made relative to this if underneath it, else
  absolute. If font is not none, generate columns for the text rendered in the
  font before other columns.  Dir_infos is the list of DirInfos in column
  order.  Keys is the list of canonical emoji sequences in row order.  Aliases
  and excluded indicate images we expect to not be present either because
  they are aliased or specifically excluded.  If annotations is not none,
  highlight sequences that appear in this map based on their map values ('ok',
  'error', 'warning').  If standalone is true, the image data and font (if used)
  will be copied under the basedir to make a completely stand-alone page.
  Colors is the list of background colors, the last DirInfo column will be
  repeated against each of these backgrounds.
  """

  basedir = path.abspath(path.expanduser(basedir))
  if not path.isdir(basedir):
    os.makedirs(basedir)

  basepaths = []

  if standalone:
    # auxiliary images are used in the decomposition of multi-part emoji but
    # aren't part of main set.  e.g. if we have female basketball player
    # color-3 we want female, basketball player, and color-3 images available
    # even if they aren't part of the target set.
    aux_info = _collect_aux_info(dir_infos, keys)

    # create image subdirectories in target dir, copy image files to them,
    # and adjust paths
    for i, info in enumerate(dir_infos):
      subdir = '%02d' % i
      dstdir = path.join(basedir, subdir)
      if not path.isdir(dstdir):
        os.mkdir(dstdir)

      copy_keys = set(keys) | aux_info[i]
      srcdir = info.directory
      filemap = info.filemap
      for key in copy_keys:
        if key in filemap:
          filename = filemap[key]
          srcfile = path.join(srcdir, filename)
          dstfile = path.join(dstdir, filename)
          shutil.copy2(srcfile, dstfile)
      basepaths.append(subdir)
  else:
    for srcdir, _, _ in dir_infos:
      abs_srcdir = path.abspath(path.expanduser(srcdir))
      if abs_srcdir == basedir:
        dirspec = ''
      elif abs_srcdir.startswith(basedir):
        dirspec = abs_srcdir[len(basedir) + 1:]
      else:
        dirspec = abs_srcdir
      basepaths.append(dirspec)

  lines = ['<table>']
  header_row = ['']
  if font:
    header_row.extend(['Emoji ltr', 'Emoji rtl'])
  header_row.extend([info.title for info in dir_infos])
  if len(colors) > 1:
    header_row.extend([dir_infos[-1].title] * (len(colors) - 1))
  header_row.extend(['Sequence', 'Name'])
  lines.append('<th>'.join(header_row))

  for key in keys:
    row = _generate_row_cells(
        key, font, aliases, excluded, dir_infos, basepaths, colors)
    row.append(_get_desc(key, aliases, dir_infos, basepaths))
    row.append(_get_name(key, annotations))
    lines.append(''.join(row))

  return '\n  <tr>'.join(lines) + '\n</table>'


def _get_image_data(image_dir, ext, prefix):
  """Return a map from a canonical tuple of cp sequences to a filename.

  This filters by file extension, and expects the rest of the files
  to match the prefix followed by a sequence of hex codepoints separated
  by underscore.  Files that don't match, duplicate sequences (because
  of casing), and out_of_range or empty codepoints raise an error."""

  fails = []
  result = {}
  expect_re = re.compile(r'%s([0-9A-Fa-f_]+).%s' % (prefix, ext))
  for f in sorted(glob.glob(path.join(image_dir, '*.%s' % ext))):
    filename = path.basename(f)
    m = expect_re.match(filename)
    if not m:
      if filename.startswith('unknown_flag.') or filename.startswith('p4p_'):
        continue
      fails.append('"%s" did not match: "%s"' % (expect_re.pattern, filename))
      continue
    seq = m.group(1)
    this_failed = False
    try:
      cps = tuple(int(s, 16) for s in seq.split('_'))
      for cp in cps:
        if (cp > 0x10ffff):
          fails.append('cp out of range: ' + filename)
          this_failed = True
          break
      if this_failed:
        continue
      canonical_cps = unicode_data.get_canonical_emoji_sequence(cps)
      if canonical_cps:
        # if it is unrecognized, just leave it alone, else replace with
        # canonical sequence.
        cps = canonical_cps
    except:
      fails.append('bad cp sequence: ' + filename)
      continue
    if cps in result:
      fails.append('duplicate sequence: %s and %s' (result[cps], filename))
      continue
    result[cps] = filename
  if fails:
    print('get_image_data failed (%s, %s, %s):\n  %s' % (
        image_dir, ext, prefix, '\n  '.join(fails)), file=sys.stderr)
    raise ValueError('get image data failed')
  return result


def _get_dir_infos(
    image_dirs, exts=None, prefixes=None, titles=None,
    default_ext=_default_ext, default_prefix=_default_prefix):
  """Return a list of DirInfos for the image_dirs.  When defined,
  exts, prefixes, and titles should be the same length as image_dirs.
  Titles default to using the last segments of the image_dirs,
  exts and prefixes default to the corresponding default values."""

  count = len(image_dirs)
  if not titles:
    titles = [None] * count
  elif len(titles) != count:
      raise ValueError('have %d image dirs but %d titles' % (
          count, len(titles)))
  if not exts:
    exts = [default_ext] * count
  elif len(exts) != count:
    raise ValueError('have %d image dirs but %d extensions' % (
        count, len(exts)))
  if not prefixes:
    prefixes = [default_prefix] * count
  elif len(prefixes) != count:
    raise ValueError('have %d image dirs but %d prefixes' % (
        count, len(prefixes)))

  infos = []
  for i in range(count):
    image_dir = image_dirs[i]
    title = titles[i] or path.basename(path.abspath(image_dir))
    ext = exts[i] or default_ext
    prefix = prefixes[i] or default_prefix
    filemap = _get_image_data(image_dir, ext, prefix)
    infos.append(DirInfo(image_dir, title, filemap))
  return infos


def _add_aliases(keys, aliases):
  for k, v in sorted(aliases.items()):
    k_str = unicode_data.seq_to_string(k)
    v_str = unicode_data.seq_to_string(v)
    if k in keys:
      msg = '' if v in keys else ' but it\'s not present'
      print('have alias image %s, should use %s%s' % (k_str, v_str, msg))
    elif v not in keys:
      print('can\'t use alias %s, no image matching %s' % (k_str, v_str))
  to_add = {k for k, v in aliases.items() if k not in keys and v in keys}
  return keys | to_add


def _get_keys(dir_infos, aliases, limit, all_emoji, emoji_sort, ignore_missing):
  """Return a list of the key tuples to display.  If all_emoji is
  true, start with all emoji sequences, else the sequences available
  in dir_infos (limited to the first dir_info if limit is True).
  If ignore_missing is true and all_emoji is false, ignore sequences
  that are not valid (e.g. skin tone variants of wrestlers).  If
  ignore_missing is true and all_emoji is true, ignore sequences
  for which we have no assets (e.g. newly defined emoji).  If not using
  all_emoji, aliases are included if we have a target for them.
  The result is in emoji order if emoji_sort is true, else in
  unicode codepoint order."""

  if all_emoji or ignore_missing:
    all_keys = unicode_data.get_emoji_sequences()
  if not all_emoji or ignore_missing:
    if len(dir_infos) == 1 or limit:
      avail_keys = frozenset(dir_infos[0].filemap.keys())
    else:
      avail_keys = _merge_keys([info.filemap for info in dir_infos])
    if aliases:
      avail_keys = _add_aliases(avail_keys, aliases)

  if not ignore_missing:
    keys = all_keys if all_emoji else avail_keys
  else:
    keys = set(all_keys) & avail_keys

  if emoji_sort:
    sorted_keys = unicode_data.get_sorted_emoji_sequences(keys)
  else:
    sorted_keys = sorted(keys)
  return sorted_keys


def _generate_info_text(args):
  lines = ['%s: %r' % t for t in sorted(args.__dict__.items())]
  lines.append('generated by %s on %s' % (
      path.basename(__file__), datetime.datetime.now()))
  return '\n  '.join(lines)


def _parse_annotation_file(afile):
  """Parse file and return a map from sequences to one of 'ok', 'warning',
  or 'error'.

  The file format consists of two kinds of lines.  One defines the annotation
  to apply, it consists of the text 'annotation:' followed by one of 'ok',
  'warning', or 'error'.  The other defines a sequence that should get the most
  recently defined annotation, this is a series of codepoints expressed in hex
  separated by spaces.  The initial default annotation is 'error'.  '#' starts
  a comment to end of line, blank lines are ignored.
  """

  annotations = {}
  line_re = re.compile(r'annotation:\s*(ok|warning|error)|([0-9a-f ]+)')
  annotation = 'error'
  with open(afile, 'r') as f:
    for line in f:
      line = line.strip()
      if not line or line[0] == '#':
        continue
      m = line_re.match(line)
      if not m:
        raise Exception('could not parse annotation "%s"' % line)
      new_annotation = m.group(1)
      if new_annotation:
        annotation = new_annotation
      else:
        seq = tuple([int(s, 16) for s in m.group(2).split()])
        canonical_seq = unicode_data.get_canonical_emoji_sequence(seq)
        if canonical_seq:
          seq = canonical_seq
        if seq in annotations:
          raise Exception(
              'duplicate sequence %s in annotations' %
              unicode_data.seq_to_string(seq))
        annotations[seq] = annotation
  return annotations


def _instantiate_template(template, arg_dict):
  id_regex = re.compile(r'\$([a-zA-Z0-9_]+)')
  ids = set(m.group(1) for m in id_regex.finditer(template))
  keyset = set(arg_dict.keys())
  extra_args = keyset - ids
  if extra_args:
    print((
        'the following %d args are unused:\n%s' %
        (len(extra_args), ', '.join(sorted(extra_args)))), file=sys.stderr)
  return string.Template(template).substitute(arg_dict)


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>$title</title>$fontFaceStyle
    <style>$style</style>
  </head>
  <body>
  <!--
  $info
  -->
  <h3>$title</h3>
  $content
  </body>
</html>
"""

STYLE = """
      tbody { background-color: rgb(110, 110, 110) }
      th { background-color: rgb(210, 210, 210) }
      td img { width: 64px; height: 64px }
      td:nth-last-of-type(2) {
         font-size: 18pt; font-weight: regular; background-color: rgb(210, 210, 210)
      }
      td:nth-last-of-type(2) img {
         vertical-align: bottom; width: 32px; height: 32px
      }
      td:last-of-type { background-color: white }
      td.error { background-color: rgb(250, 65, 75) }
      td.warning { background-color: rgb(240, 245, 50) }
      td.ok { background-color: rgb(10, 200, 60) }
"""

def write_html_page(
    filename, page_title, font, dir_infos, keys, aliases, excluded, annotations,
    standalone, colors, info):

  out_dir = path.dirname(filename)
  if font:
    if standalone:
      # the assumption with standalone is that the source data and
      # output directory don't overlap, this should probably be checked...

      rel_fontpath = path.join('font', path.basename(font))
      new_font = path.join(out_dir, rel_fontpath)
      tool_utils.ensure_dir_exists(path.dirname(new_font))
      shutil.copy2(font, new_font)
      font = rel_fontpath
    else:
      common_prefix, (rel_dir, rel_font) = tool_utils.commonpathprefix(
          [out_dir, font])
      if rel_dir == '':
        # font is in a subdirectory of the target, so just use the relative
        # path
        font = rel_font
      else:
        # use the absolute path
        font = path.normpath(path.join(common_prefix, rel_font))

  content = _generate_content(
      path.dirname(filename), font, dir_infos, keys, aliases, excluded,
      annotations, standalone, colors)
  N_STYLE = STYLE
  if font:
    FONT_FACE_STYLE = """
    <style>@font-face {
      font-family: "Emoji"; src: local("Noto Color Emoji"), url("%s");
    }</style>""" % font
    N_STYLE += '      span.efont { font-family: "Emoji"; font-size:32pt }\n'
  else:
    FONT_FACE_STYLE = ''
  num_final_cols = len(colors)
  col_colors = ['']
  for i, color in enumerate(colors):
    col_colors.append(
        """td:nth-last-of-type(%d) { background-color: #%s }\n""" % (
            2 + num_final_cols - i, color))
  N_STYLE += '       '.join(col_colors)
  text = _instantiate_template(
      TEMPLATE, {
          'title': page_title, 'fontFaceStyle': FONT_FACE_STYLE,
          'style': N_STYLE, 'content': content, 'info':info})
  with codecs.open(filename, 'w', 'utf-8') as f:
    f.write(text)


def _get_canonical_aliases():
  def canon(seq):
    return unicode_data.get_canonical_emoji_sequence(seq) or seq
  aliases = add_aliases.read_default_emoji_aliases()
  return {canon(k): canon(v) for k, v in aliases.items()}

def _get_canonical_excluded():
  def canon(seq):
    return unicode_data.get_canonical_emoji_sequence(seq) or seq
  aliases = add_aliases.read_default_unknown_flag_aliases()
  return frozenset([canon(k) for k in aliases.keys()])


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '-o', '--outfile', help='path to output file', metavar='file',
      required=True)
  parser.add_argument(
      '--page_title', help='page title', metavar='title', default='Emoji Table')
  parser.add_argument(
      '-d', '--image_dirs', help='image directories', metavar='dir',
      nargs='+')
  parser.add_argument(
      '-e', '--exts', help='file extension, one per image dir', metavar='ext',
      nargs='*')
  parser.add_argument(
      '-p', '--prefixes', help='file name prefix, one per image dir',
      metavar='prefix', nargs='*')
  parser.add_argument(
      '-t', '--titles', help='title, one per image dir', metavar='title',
      nargs='*'),
  parser.add_argument(
      '-l', '--limit', help='limit to only sequences supported by first set',
      action='store_true')
  parser.add_argument(
      '-de', '--default_ext', help='default extension', metavar='ext',
      default=_default_ext)
  parser.add_argument(
      '-dp', '--default_prefix', help='default prefix', metavar='prefix',
      default=_default_prefix)
  parser.add_argument(
      '-f', '--font', help='emoji font', metavar='font')
  parser.add_argument(
      '-a', '--annotate', help='file listing sequences to annotate',
      metavar='file')
  parser.add_argument(
      '-s', '--standalone', help='copy resources used by html under target dir',
      action='store_true')
  parser.add_argument(
      '-c', '--colors', help='list of colors for background', nargs='*',
      metavar='hex')
  parser.add_argument(
      '--all_emoji', help='use all emoji sequences', action='store_true')
  parser.add_argument(
      '--emoji_sort', help='use emoji sort order', action='store_true')
  parser.add_argument(
      '--ignore_missing', help='do not include missing emoji',
      action='store_true')

  args = parser.parse_args()
  file_parts = path.splitext(args.outfile)
  if file_parts[1] != '.html':
    args.outfile = file_parts[0] + '.html'
    print('added .html extension to filename:\n%s' % args.outfile)

  if args.annotate:
    annotations = _parse_annotation_file(args.annotate)
  else:
    annotations = None

  if args.colors == None:
    args.colors = ['6e6e6e']
  elif not args.colors:
    args.colors = """eceff1 f5f5f5 e4e7e9 d9dbdd 080808 263238 21272b 3c474c
    4db6ac 80cbc4 5e35b1""".split()

  dir_infos = _get_dir_infos(
      args.image_dirs, args.exts, args.prefixes, args.titles,
      args.default_ext, args.default_prefix)

  aliases = _get_canonical_aliases()
  keys = _get_keys(
      dir_infos, aliases, args.limit, args.all_emoji, args.emoji_sort,
      args.ignore_missing)

  excluded = _get_canonical_excluded()

  info = _generate_info_text(args)

  write_html_page(
      args.outfile, args.page_title, args.font, dir_infos, keys, aliases,
      excluded, annotations, args.standalone, args.colors, info)


if __name__ == "__main__":
  main()
