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
from os import path
import re
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

def _generate_row_cells(key, dir_infos):
  CELL_PREFIX = '<td>'
  def _cell(key, info):
    if key in info.filemap:
      return '<img src="%s">' % path.join(
          info.directory, info.filemap[key])
    return '-missing-'
  return [CELL_PREFIX + _cell(key, info) for info in dir_infos]


def _get_desc(key_tuple, dir_infos):
  CELL_PREFIX = '<td class="desc">'
  def _get_filepath(cp):
    cp_key = tuple([cp])
    for info in dir_infos:
      if cp_key in info.filemap:
        return path.join(info.directory, info.filemap[cp_key])
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


def _get_name(key_tuple):
  CELL_PREFIX = '<td class="name">'
  if len(key_tuple) != 1:
    name = ''
  else:
    cp = key_tuple[0]
    if cp in unicode_data.proposed_emoji_cps():
      name = '(proposed) ' + unicode_data.proposed_emoji_name(cp)
    else:
      name =unicode_data.name(cp, '(error)')
  return CELL_PREFIX + name


def _generate_content(dir_infos):
  """Generate an html table for the infos."""
  lines = ['<table>']
  header_row = ['']
  header_row.extend([info.title for info in dir_infos])
  header_row.extend(['Description', 'Name'])
  lines.append('<th>'.join(header_row))

  all_keys = _merge_keys([info.filemap for info in dir_infos])
  for key in sorted(all_keys):
    row = []
    row.extend(_generate_row_cells(key, dir_infos))
    row.append(_get_desc(key, dir_infos))
    row.append(_get_name(key))
    lines.append(''.join(row))
  return '\n  <tr>'.join(lines) + '\n</table>'


"""
def _generate_content(files, prefix=_default_prefix):
  key_to_filename = {}
  for fname in files:
    filename = path.basename(fname)
    if not filename.startswith(prefix):
      print >> sys.stderr, 'bad prefix for filename %s' % fname
      continue
    key_string = path.splitext(filename)[0]
    key_string = key_string[len(prefix):]
    try:
      key_tuple = tuple(int(k, 16) for k in key_string.split('_'))
    except:
      print 'bad filename: "%s"' % key_string
    key_to_filename[key_tuple] = fname

  lines = ["<table>"]
  for key_tuple in sorted(key_to_filename):
    if len(key_tuple) == 1:
      key_string = 'U+%04X' % key_tuple
    else:
      key_string = ' + '.join(
          '<img src="%s">' % key_to_filename[tuple([key])]
          for key in key_tuple
          if tuple([key]) in key_to_filename)
    name = _get_name(key_tuple)
    lines.append('<tr><td><img src="%s"><td class="desc">'
                 '%s<td class="name">'
                 '%s' % (
        key_to_filename[key_tuple], key_string, name))
  return '\n  '.join(lines) + '\n<table>'
"""

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
      if filename.startswith('unknown_flag.'):
        continue
      fails.append('"%s" did not match: "%s"' % (expect_re, filename))
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
    title = titles[i] or path.basename(path.normpath(image_dir))
    ext = exts[i] or default_ext
    prefix = prefixes[i] or default_prefix
    filemap = _get_image_data(image_dir, ext, prefix)
    infos.append(DirInfo(image_dir, title, filemap))
  return infos


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
    <title>{{title}}</title>
    <style>{{style}}</style>
  </head>
  <body>
  {{content}}
  </body>
</html>
"""

STYLE = """
      tbody { background-color: rgb(210, 210, 210) }
      tbody img { width: 64px; height: 64px }
      tbody .desc { font-size: 20pt; font-weight: bold }
      tbody .desc img { vertical-align: middle; width: 32px; height: 32px }
      tbody .name { background-color: white }
"""

def write_html_page(filename, page_title, dir_infos):
  content = _generate_content(dir_infos)
  text = _instantiate_template(
      TEMPLATE, {'title': page_title, 'style': STYLE, 'content': content})
  with codecs.open(filename, 'w', 'utf-8') as f:
    f.write(text)


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument(
      'filename', help='path to output file', metavar='filename')
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
      '-de', '--default_ext', help='default extension', metavar='ext',
      default=_default_ext)
  parser.add_argument(
      '-dp', '--default_prefix', help='default prefix', metavar='prefix',
      default=_default_prefix)

  args = parser.parse_args()
  file_parts = path.splitext(args.filename)
  if file_parts[1] != 'html':
    args.filename = file_parts[0] + '.html'
    print 'added .html extension to filename:\n%s' % args.filename

  dir_infos = _get_dir_infos(
      args.image_dirs, args.exts, args.prefixes, args.titles, args.default_ext,
      args.default_prefix)

  write_html_page(args.filename, args.page_title, dir_infos)


if __name__ == "__main__":
    main()
