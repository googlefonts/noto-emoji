#!/usr/bin/python
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

import argparse
import codecs
import collections
import glob
import os
from os import path
import re
import shutil
import sys
from nototools import unicode_data

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

def _generate_row_cells(key, font, dir_infos, basepaths):
  CELL_PREFIX = '<td>'
  indices = range(len(basepaths))
  def _cell(key, info, basepath):
    if key in info.filemap:
      return '<img src="%s">' % path.join(
          basepath, info.filemap[key])
    return '-missing-'
  def _text_cell(key, text_dir):
    def _cp_seq(cp):
      # comment this out for now
      if False and cp in [ord('*'), 0x2640, 0x2642, 0x2695]:
        return unichr(cp) + unichr(0xfe0f)
      else:
        return unichr(cp)
    text = ''.join(_cp_seq(cp) for cp in key)
    return '<span class="efont" dir="%s">%s</span>' % (text_dir, text)

  if font:
    row_cells = [
        CELL_PREFIX + _text_cell(key, text_dir)
        for text_dir in ('ltr', 'rtl')]
  else:
    row_cells = []
  row_cells.extend(
      [CELL_PREFIX + _cell(key, dir_infos[i], basepaths[i])
       for i in indices])
  return row_cells


def _get_desc(key_tuple, dir_infos, basepaths):
  CELL_PREFIX = '<td>'
  def _get_filepath(cp):
    cp_key = tuple([cp])
    for i in range(len(dir_infos)):
      info = dir_infos[i]
      if cp_key in info.filemap:
        basepath = basepaths[i]
        return path.join(basepath, info.filemap[cp_key])
    return None

  def _get_part(cp):
    if cp == 0x200d:  # zwj, common so replace with '+'
      return '+'
    if cp == 0xfe0f:  # emoji variation selector, we ignore it
      return None
    fname = _get_filepath(cp)
    if fname:
      return '<img src="%s">' % fname
    return '%04X' % cp

  if len(key_tuple) == 1:
    desc = 'U+%04X' % key_tuple
  else:
    desc = ' '.join(filter(None, [_get_part(cp) for cp in key_tuple]))
  return CELL_PREFIX + desc


def _get_name(key_tuple, annotated_tuples):
  CELL_PREFIX = '<td%s>' % (
      '' if annotated_tuples is None or key_tuple not in annotated_tuples
      else ' class="aname"')

  if len(key_tuple) != 1:
    name = '(' + ' '.join('U+%04X' % cp for cp in key_tuple) + ')'
  else:
    cp = key_tuple[0]
    if cp in unicode_data.proposed_emoji_cps():
      name = '(proposed) ' + unicode_data.proposed_emoji_name(cp)
    else:
      name = unicode_data.name(cp, '(error)')
  return CELL_PREFIX + name


def _collect_aux_info(dir_infos, all_keys):
  """Returns a map from dir_info_index to a set of keys of additional images
  that we will take from the directory at that index."""

  target_key_to_info_index = {}
  for key in all_keys:
    if len(key) == 1:
      continue
    for cp in key:
      target_key = tuple([cp])
      if target_key in all_keys or target_key in target_key_to_info_index:
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
  for key, index in target_key_to_info_index.iteritems():
    aux_info[index].add(key)

  return aux_info


def _generate_content(basedir, font, dir_infos, limit, annotate, standalone):
  """Generate an html table for the infos.  basedir is the parent directory
  of the content, filenames will be made relative to this if underneath it,
  else absolute. If limit is true and there are multiple dirs, limit the set of
  sequences to those in the first dir.  If font is not none, generate columns
  for the text rendered in the font before other columns.  if annotate is
  not none, highlight sequences that appear in this set."""

  if len(dir_infos) == 1 or limit:
    all_keys = frozenset(dir_infos[0].filemap.keys())
  else:
    all_keys = _merge_keys([info.filemap for info in dir_infos])

  basedir = path.abspath(path.expanduser(basedir))
  if not path.isdir(basedir):
    os.makedirs(basedir)

  basepaths = []

  if standalone:
    # auxiliary images are used in the decomposition of multi-part emoji but
    # aren't part of main set.  e.g. if we have female basketball player
    # color-3 we want female, basketball player, and color-3 images available
    # even if they aren't part of the target set.
    aux_info = _collect_aux_info(dir_infos, all_keys)

    # create image subdirectories in target dir, copy image files to them,
    # and adjust paths
    for i, info in enumerate(dir_infos):
      subdir = '%02d' % i
      dstdir = path.join(basedir, subdir)
      if not path.isdir(dstdir):
        os.mkdir(dstdir)

      aux_keys = aux_info[i]
      copy_keys = all_keys if not aux_keys else (all_keys | aux_keys)
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
        dirspec = abs_filedir[len(abs_basedir) + 1:]
      else:
        dirspec = abs_filedir
      basepaths.append(dirspec)

  lines = ['<table>']
  header_row = ['']
  if font:
    header_row.extend(['Emoji ltr', 'Emoji rtl'])
  header_row.extend([info.title for info in dir_infos])
  header_row.extend(['Description', 'Name'])
  lines.append('<th>'.join(header_row))

  for key in sorted(all_keys):
    row = []
    row.extend(_generate_row_cells(key, font, dir_infos, basepaths))
    row.append(_get_desc(key, dir_infos, basepaths))
    row.append(_get_name(key, annotate))
    lines.append(''.join(row))
  return '\n  <tr>'.join(lines) + '\n</table>'


def _get_image_data(image_dir, ext, prefix):
  """Return a map from a tuple of cp sequences to a filename.

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
    try:
      cps = tuple(int(s, 16) for s in seq.split('_'))
    except:
      fails.append('bad cp sequence: ' + filename)
      continue
    this_failed = False
    for cp in cps:
      if (cp > 0x10ffff):
        fails.append('cp out of range: ' + filename)
        this_failed = True
        break
    if this_failed:
      continue
    if cps in result:
      fails.append('duplicate sequence: %s and %s' (result[cps], filename))
      continue
    result[cps] = filename
  if fails:
    print >> sys.stderr, 'get_image_data failed (%s, %s, %s):\n  %s' % (
        image_dir, ext, prefix, '\n  '.join(fails))
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


def _parse_annotation_file(afile):
  annotations = set()
  line_re = re.compile(r'([0-9a-f ]+)')
  with open(afile, 'r') as f:
    for line in f:
      line = line.strip()
      if not line or line[0] == '#':
        continue
      m = line_re.match(line)
      if m:
        annotations.add(tuple([int(s, 16) for s in m.group(1).split()]))
  return frozenset(annotations)


def _instantiate_template(template, arg_dict):
  id_regex = re.compile('{{([a-zA-Z0-9_]+)}}')
  ids = set(m.group(1) for m in id_regex.finditer(template))
  keyset = set(arg_dict.keys())
  missing_ids = ids - keyset
  extra_args = keyset - ids
  if extra_args:
    print >> sys.stderr, (
        'the following %d args are unused:\n%s' %
        (len(extra_args), ', '.join(sorted(extra_args))))
  text = template
  if missing_ids:
    raise ValueError(
        'the following %d ids in the template have no args:\n%s' %
        (len(missing_ids), ', '.join(sorted(missing_ids))))
  for arg in ids:
    text = re.sub('{{%s}}' % arg, arg_dict[arg], text)
  return text


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>{{title}}</title>{{fontFaceStyle}}
    <style>{{style}}</style>
  </head>
  <body>
  {{content}}
  </body>
</html>
"""

STYLE = """
      tbody { background-color: rgb(110, 110, 110) }
      th { background-color: rgb(210, 210, 210) }
      td img { width: 64px; height: 64px }
      td:nth-last-of-type(2) {
         font-size: 20pt; font-weight: bold; background-color: rgb(210, 210, 210)
      }
      td:nth-last-of-type(2) img {
         vertical-align: middle; width: 32px; height: 32px
      }
      td:last-of-type { background-color: white }
      td.aname { background-color: rgb(250, 65, 75) }
"""

def write_html_page(
    filename, page_title, font, dir_infos, limit, annotate, standalone):
  content = _generate_content(
      path.dirname(filename), font, dir_infos, limit, annotate, standalone)
  N_STYLE = STYLE
  if font:
    FONT_FACE_STYLE = """
    <style>@font-face {
      font-family: "Emoji"; src: url("%s");
    }</style>""" % font
    N_STYLE += '      span.efont { font-family: "Emoji"; font-size:32pt }\n'
  else:
    FONT_FACE_STYLE = ''
  text = _instantiate_template(
      TEMPLATE, {
          'title': page_title, 'fontFaceStyle': FONT_FACE_STYLE,
          'style': N_STYLE, 'content': content})
  with codecs.open(filename, 'w', 'utf-8') as f:
    f.write(text)


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

  args = parser.parse_args()
  file_parts = path.splitext(args.outfile)
  if file_parts[1] != '.html':
    args.outfile = file_parts[0] + '.html'
    print 'added .html extension to filename:\n%s' % args.outfile

  if args.annotate:
    annotations = _parse_annotation_file(args.annotate)
  else:
    annotations = None

  dir_infos = _get_dir_infos(
      args.image_dirs, args.exts, args.prefixes, args.titles,
      args.default_ext, args.default_prefix)

  write_html_page(
      args.outfile, args.page_title, args.font, dir_infos, args.limit,
      annotations, args.standalone)


if __name__ == "__main__":
    main()
