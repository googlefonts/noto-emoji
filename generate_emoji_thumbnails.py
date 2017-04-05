#!/usr/bin/env python
# Copyright 2017 Google Inc. All rights reserved.
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

"""Generate 72x72 thumbnails including aliases.

Takes a source directory of images named using our emoji filename
conventions and writes thumbnails of them into the destination
directory.  If a file is a target of one or more aliases, creates
copies named for the aliases."""


import argparse
import collections
import logging
import os
from os import path
import shutil
import subprocess

import add_aliases

from nototools import tool_utils

logger = logging.getLogger('emoji_thumbnails')

def create_thumbnail(src_path, dst_path):
  # uses imagemagik
  subprocess.check_call(['convert', '-resize', '72x72', src_path, dst_path])
  logger.info('wrote thumbnail: %s' % dst_path)


_INV_ALIASES = None
def get_inv_aliases():
  global _INV_ALIASES
  if _INV_ALIASES is None:
    aliases = add_aliases.read_default_emoji_aliases()
    inv_aliases = collections.defaultdict(list)
    for k, v in aliases.iteritems():
      inv_aliases[v].append(k)
    _INV_ALIASES = inv_aliases
  return _INV_ALIASES


def is_emoji_filename(filename):
  return filename.startswith('emoji_u') and filename.endswith('.png')


def check_emoji_filename(filename):
  if not is_emoji_filename(filename):
    raise ValueError('not an emoji image file: %s' % filename)


def emoji_filename_to_sequence(filename):
  check_emoji_filename(filename)

  return tuple([
      int(s, 16) for s in filename[7:-4].split('_')
      if s.lower() != 'fe0f'])


def sequence_to_emoji_filename(seq):
  return 'emoji_u%s.png' % '_'.join('%04x' % n for n in seq)


def create_emoji_alias(src_path, dst_dir):
  """If src_path is a target of any emoji aliases, create a copy in dst_dir
  named for each alias."""
  src_file = path.basename(src_path)
  seq = emoji_filename_to_sequence(src_file)

  inv_aliases = get_inv_aliases()
  if seq in inv_aliases:
    for alias_seq in inv_aliases[seq]:
      alias_file = sequence_to_emoji_filename(alias_seq)
      shutil.copy2(src_path, path.join(dst_dir, alias_file))
      logger.info('wrote alias %s (copy of %s)' % (alias_file, src_file))


def create_thumbnails_and_aliases(src_dir, dst_dir):
  if not path.isdir(src_dir):
    raise ValueError('"%s" is not a directory')
  dst_dir = tool_utils.ensure_dir_exists(dst_dir)

  for f in os.listdir(src_dir):
    if not (f.startswith('emoji_u') and f.endswith('.png')):
      logger.warning('skipping "%s"' % f)
      continue
    src = path.join(src_dir, f)
    dst = path.join(dst_dir, f)
    create_thumbnail(src, dst)
    create_emoji_alias(dst, dst_dir)


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '-s', '--src_dir', help='source images', metavar='dir', required=True)
  parser.add_argument(
      '-d', '--dst_dir', help='destination directory', metavar='dir',
      required=True)
  parser.add_argument(
      '-v', '--verbose', help='write log output', metavar='level',
      choices='warning info debug'.split(), const='info',
      nargs='?')
  args = parser.parse_args()

  if args.verbose is not None:
    logging.basicConfig(level=getattr(logging, args.verbose.upper()))

  create_thumbnails_and_aliases(args.src_dir, args.dst_dir)


if __name__ == '__main__':
  main()
