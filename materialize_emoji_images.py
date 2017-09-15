#!/usr/bin/env python
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

"""Create a copy of the emoji images that instantiates aliases, etc. as
symlinks."""
from __future__ import print_function

import argparse
import glob
import os
from os import path
import re
import shutil

from nototools import tool_utils

# copied from third_party/color_emoji/add_glyphs.py

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

OMITTED_FLAGS = set(
    'BL BQ DG EA EH FK GF GP GS MF MQ NC PM RE TF WF XK YT'.split())

def _flag_str(ris_pair):
  return '_'.join('%04x' % (ord(cp) - ord('A') +  0x1f1e6)
                  for cp in ris_pair)

def _copy_files(src, dst):
  """Copies files named 'emoji_u*.png' from dst to src, and return a set of
  the names with 'emoji_u' and the extension stripped."""
  code_strings = set()
  tool_utils.check_dir_exists(src)
  dst = tool_utils.ensure_dir_exists(dst, clean=True)
  for f in glob.glob(path.join(src, 'emoji_u*.png')):
    shutil.copy(f, dst)
    code_strings.add(path.splitext(path.basename(f))[0][7:])
  return code_strings


def _alias_people(code_strings, dst):
  """Create aliases for people in dst, based on code_strings."""
  for src, ali in sorted(EXTRA_SEQUENCES.items()):
    if src[1:].lower() in code_strings:
      src_name = 'emoji_%s.png' % src.lower()
      ali_name = 'emoji_u%s.png' % ali.lower()
      print('creating symlink %s -> %s' % (ali_name, src_name))
      os.symlink(path.join(dst, src_name), path.join(dst, ali_name))
    else:
      print('people image %s not found' % src, file=os.stderr)


def _alias_flags(code_strings, dst):
  for ali, src in sorted(FLAG_ALIASES.items()):
    src_str = _flag_str(src)
    if src_str in code_strings:
      src_name = 'emoji_u%s.png' % src_str
      ali_name = 'emoji_u%s.png' % _flag_str(ali)
      print('creating symlink %s (%s) -> %s (%s)' % (ali_name, ali, src_name, src))
      os.symlink(path.join(dst, src_name), path.join(dst, ali_name))
    else:
      print('flag image %s (%s) not found' % (src_name, src), file=os.stderr)


def _alias_omitted_flags(code_strings, dst):
  UNKNOWN_FLAG = 'fe82b'
  if UNKNOWN_FLAG not in code_strings:
    print('unknown flag missing', file=os.stderr)
    return
  dst_name = 'emoji_u%s.png' % UNKNOWN_FLAG
  dst_path = path.join(dst, dst_name)
  for ali in sorted(OMITTED_FLAGS):
    ali_str = _flag_str(ali)
    if ali_str in code_strings:
      print('omitted flag %s has image %s' % (ali, ali_str), file=os.stderr)
      continue
    ali_name = 'emoji_u%s.png' % ali_str
    print('creating symlink %s (%s) -> unknown_flag (%s)' % (
        ali_str, ali, dst_name))
    os.symlink(dst_path, path.join(dst, ali_name))


def materialize_images(src, dst):
  code_strings = _copy_files(src, dst)
  _alias_people(code_strings, dst)
  _alias_flags(code_strings, dst)
  _alias_omitted_flags(code_strings, dst)

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '-s', '--srcdir', help='path to input sources', metavar='dir',
      default = 'build/compressed_pngs')
  parser.add_argument(
      '-d', '--dstdir', help='destination for output images', metavar='dir')
  args = parser.parse_args()
  materialize_images(args.srcdir, args.dstdir)


if __name__ == '__main__':
  main()
