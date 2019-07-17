#!/usr/bin/env python3
#
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

from __future__ import print_function
import argparse
import glob
import os
from os import path
import sys

"""Rename image files based on codepoints to remove the emoji variation
selector from the name.  For our emoji image data, this codepoint is not
relevant."""

EMOJI_VS = 0xfe0f


def str_to_seq(seq_str):
  return tuple([int(s, 16) for s in seq_str.split('_')])


def seq_to_str(seq):
  return '_'.join('%04x' % cp for cp in seq)


def strip_vs(seq):
  return tuple([cp for cp in seq if cp != EMOJI_VS])


def strip_vs_from_filenames(imagedir, prefix, ext, dry_run=False):
  prefix_len = len(prefix)
  suffix_len = len(ext) + 1
  names = [path.basename(f)
           for f in glob.glob(
               path.join(imagedir, '%s*.%s' % (prefix, ext)))]
  renames = {}
  for name in names:
    seq = str_to_seq(name[prefix_len:-suffix_len])
    if seq and EMOJI_VS in seq:
      newname = '%s%s.%s' % (prefix, seq_to_str(strip_vs(seq)), ext)
      if newname in names:
        print('%s non-vs name %s already exists.' % (
            name, newname), file=sys.stderr)
        return
      renames[name] = newname

  for k, v in renames.iteritems():
    if dry_run:
      print('%s -> %s' % (k, v))
    else:
      os.rename(path.join(imagedir, k), path.join(imagedir, v))
  print('renamed %d files in %s' % (len(renames), imagedir))


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '-d', '--imagedir', help='directory containing images to rename',
      metavar='dir', required=True)
  parser.add_argument(
      '-e', '--ext', help='image filename extension (default png)',
      choices=['ai', 'png', 'svg'], default='png')
  parser.add_argument(
      '-p', '--prefix', help='image filename prefix (default emoji_u)',
      default='emoji_u', metavar='pfx')
  parser.add_argument(
      '-n', '--dry_run', help='compute renames and list only',
      action='store_true')

  args = parser.parse_args()
  strip_vs_from_filenames(args.imagedir, args.prefix, args.ext, args.dry_run)


if __name__ == '__main__':
  main()
