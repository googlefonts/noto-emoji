#!/usr/bin/env python3
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
from nototools import unicode_data

logger = logging.getLogger('emoji_thumbnails')

def create_thumbnail(src_path, dst_path, crop):
  # Uses imagemagik
  # We need images exactly 72x72 in size, with transparent background.
  # Remove 4-pixel LR margins from 136x128 source images if we crop.
  if crop:
    cmd = [
        'convert', src_path, '-crop', '128x128+4+0!', '-thumbnail', '72x72',
        'PNG32:' + dst_path]
  else:
    cmd = [
        'convert', '-thumbnail', '72x72', '-gravity', 'center', '-background',
        'none', '-extent', '72x72', src_path, 'PNG32:' + dst_path]
  subprocess.check_call(cmd)


def get_inv_aliases():
  """Return a mapping from target to list of sources for all alias
  targets in either the default alias table or the unknown_flag alias
  table."""

  inv_aliases = collections.defaultdict(list)

  standard_aliases = add_aliases.read_default_emoji_aliases()
  for k, v in standard_aliases.iteritems():
    inv_aliases[v].append(k)

  unknown_flag_aliases = add_aliases.read_emoji_aliases(
      'unknown_flag_aliases.txt')
  for k, v in unknown_flag_aliases.iteritems():
    inv_aliases[v].append(k)

  return inv_aliases


def filename_to_sequence(filename, prefix, suffix):
  if not filename.startswith(prefix) and filename.endswith(suffix):
    raise ValueError('bad prefix or suffix: "%s"' % filename)
  seq_str = filename[len(prefix): -len(suffix)]
  seq = unicode_data.string_to_seq(seq_str)
  if not unicode_data.is_cp_seq(seq):
    raise ValueError('sequence includes non-codepoint: "%s"' % filename)
  return seq


def sequence_to_filename(seq, prefix, suffix):
  return ''.join((prefix, unicode_data.seq_to_string(seq), suffix))


def create_thumbnails_and_aliases(src_dir, dst_dir, crop, dst_prefix):
  """Creates thumbnails in dst_dir based on sources in src.dir, using
  dst_prefix. Assumes the source prefix is 'emoji_u' and the common suffix
  is '.png'."""

  src_dir = tool_utils.resolve_path(src_dir)
  if not path.isdir(src_dir):
    raise ValueError('"%s" is not a directory')

  dst_dir = tool_utils.ensure_dir_exists(tool_utils.resolve_path(dst_dir))

  src_prefix = 'emoji_u'
  suffix = '.png'

  inv_aliases = get_inv_aliases()

  for src_file in os.listdir(src_dir):
    try:
      seq = unicode_data.strip_emoji_vs(
          filename_to_sequence(src_file, src_prefix, suffix))
    except ValueError as ve:
      logger.warning('Error (%s), skipping' % ve)
      continue

    src_path = path.join(src_dir, src_file)

    dst_file = sequence_to_filename(seq, dst_prefix, suffix)
    dst_path = path.join(dst_dir, dst_file)

    create_thumbnail(src_path, dst_path, crop)
    logger.info('wrote thumbnail%s: %s' % (
        ' with crop' if crop else '', dst_file))

    for alias_seq in inv_aliases.get(seq, ()):
      alias_file = sequence_to_filename(alias_seq, dst_prefix, suffix)
      alias_path = path.join(dst_dir, alias_file)
      shutil.copy2(dst_path, alias_path)
      logger.info('wrote alias: %s' % alias_file)


def main():
  SRC_DEFAULT = '[emoji]/build/compressed_pngs'
  PREFIX_DEFAULT = 'android_'

  parser = argparse.ArgumentParser()
  parser.add_argument(
      '-s', '--src_dir', help='source images (default \'%s\')' % SRC_DEFAULT,
      default=SRC_DEFAULT, metavar='dir')
  parser.add_argument(
      '-d', '--dst_dir', help='destination directory', metavar='dir',
      required=True)
  parser.add_argument(
      '-p', '--prefix', help='prefix for thumbnail (default \'%s\')' %
      PREFIX_DEFAULT, default=PREFIX_DEFAULT, metavar='str')
  parser.add_argument(
      '-c', '--crop', help='crop images (will automatically crop if '
      'src dir is the default)', action='store_true')
  parser.add_argument(
      '-v', '--verbose', help='write log output', metavar='level',
      choices='warning info debug'.split(), const='info',
      nargs='?')
  args = parser.parse_args()

  if args.verbose is not None:
    logging.basicConfig(level=getattr(logging, args.verbose.upper()))

  crop = args.crop or (args.src_dir == SRC_DEFAULT)
  create_thumbnails_and_aliases(
      args.src_dir, args.dst_dir, crop, args.prefix)


if __name__ == '__main__':
  main()
