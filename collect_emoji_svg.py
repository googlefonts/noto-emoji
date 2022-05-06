#!/usr/bin/env python3
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

"""Tool to collect emoji svg glyphs into one directory for processing
by add_svg_glyphs.  There are two sources, noto/color_emoji/svg and
noto/third_party/region-flags/svg.  The add_svg_glyphs file expects
the file names to contain the character string that represents it
represented as a sequence of hex-encoded codepoints separated by
underscore.  The files in noto/color_emoji/svg do this, and have the
prefix 'emoji_u', but the files in region-flags/svg just have the
two-letter code.

We create a directory and copy the files into it with the required
naming convention. First we do this for region-flags/svg, converting
the names, and then we do this for color_emoji/svg, so any duplicates
will be overwritten by what we assume are the preferred svg.  We use
copies instead of symlinks so we can continue to optimize or modify
the files without messing with the originals."""

import argparse
import glob
import logging
import os
import os.path
import re
import shutil
import sys

from nototools import tool_utils

def _is_svg(f):
  return f.endswith('.svg')


def _is_svg_and_startswith_emoji(f):
  return f.endswith('.svg') and f.startswith('emoji_u')


def _flag_rename(f):
  """Converts a file name from two-letter upper-case ASCII to our expected
  'emoji_uXXXXX_XXXXX form, mapping each character to the corresponding
  regional indicator symbol."""

  cp_strs = []
  name, ext = os.path.splitext(f)
  if len(name) != 2:
    raise ValueError('illegal flag name "%s"' % f)
  for cp in name:
    if not ('A' <= cp <= 'Z'):
      raise ValueError('illegal flag name "%s"' % f)
    ncp = 0x1f1e6 - 0x41 + ord(cp)
    cp_strs.append("%04x" % ncp)
  return 'emoji_u%s%s' % ('_'.join(cp_strs), ext)


def copy_with_rename(src_dir, dst_dir, accept_pred=None, rename=None):
  """Copy files from src_dir to dst_dir that match accept_pred (all if None) and
  rename using rename (if not None), replacing existing files.  accept_pred
  takes the filename and returns True if the file should be copied, rename takes
  the filename and returns a new file name."""

  count = 0
  replace_count = 0
  for src_filename in os.listdir(src_dir):
    if accept_pred and not accept_pred(src_filename):
      continue
    dst_filename = rename(src_filename) if rename else src_filename
    src = os.path.join(src_dir, src_filename)
    dst = os.path.join(dst_dir, dst_filename)
    if os.path.exists(dst):
      logging.debug('Replacing existing file %s', dst)
      os.unlink(dst)
      replace_count += 1
    shutil.copy2(src, dst)
    logging.debug('cp -p %s %s', src, dst)
    count += 1
  if logging.getLogger().getEffectiveLevel() <= logging.INFO:
    src_short = tool_utils.short_path(src_dir)
    dst_short = tool_utils.short_path(dst_dir)
    logging.info('Copied %d files (replacing %d) from %s to %s',
        count, replace_count, src_short, dst_short)


def build_svg_dir(dst_dir, clean=False, emoji_dir='', flags_dir=''):
  """Copies/renames files from emoji_dir and then flags_dir, giving them the
  standard format and prefix ('emoji_u' followed by codepoints expressed in hex
  separated by underscore).  If clean, removes the target dir before proceeding.
  If either emoji_dir or flags_dir are empty, skips them."""

  dst_dir = tool_utils.ensure_dir_exists(dst_dir, clean=clean)

  if not emoji_dir and not flags_dir:
    logging.warning('Nothing to do.')
    return

  if emoji_dir:
    copy_with_rename(
        emoji_dir, dst_dir, accept_pred=_is_svg_and_startswith_emoji)

  if flags_dir:
     copy_with_rename(
        flags_dir, dst_dir, accept_pred=_is_svg, rename=_flag_rename)


def main(argv):
  DEFAULT_EMOJI_DIR = '[emoji]/svg'
  DEFAULT_FLAGS_DIR = '[emoji]/third_party/region-flags/svg'

  parser = argparse.ArgumentParser(
      description='Collect svg files into target directory with prefix.')
  parser.add_argument(
      'dst_dir', help='Directory to hold copied files.', metavar='dir')
  parser.add_argument(
      '--clean', '-c', help='Replace target directory', action='store_true')
  parser.add_argument(
      '--flags_dir', '-f', metavar='dir', help='directory containing flag svg, '
      'default %s' % DEFAULT_FLAGS_DIR, default=DEFAULT_FLAGS_DIR)
  parser.add_argument(
      '--emoji_dir', '-e', metavar='dir',
      help='directory containing emoji svg, default %s' % DEFAULT_EMOJI_DIR,
      default=DEFAULT_EMOJI_DIR)
  parser.add_argument(
      '-l', '--loglevel', help='log level name/value', default='warning')
  args = parser.parse_args(argv)

  tool_utils.setup_logging(args.loglevel)

  args.flags_dir = tool_utils.resolve_path(args.flags_dir)
  args.emoji_dir = tool_utils.resolve_path(args.emoji_dir)
  build_svg_dir(
      args.dst_dir, clean=args.clean, emoji_dir=args.emoji_dir,
      flags_dir=args.flags_dir)


if __name__ == '__main__':
  main(sys.argv[1:])
