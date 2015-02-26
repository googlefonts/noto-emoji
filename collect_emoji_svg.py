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
import os
import os.path
import re
import shutil
import sys

def _is_svg(f):
  return f.endswith('.svg')


def _is_svg_and_startswith_emoji(f):
  return f.endswith('.svg') and f.startswith('emoji_u')


def _flag_rename(f):
  """Converts file names from region-flags files (upper-case ASCII) to our expected
  'encoded-codepoint-ligature' form, mapping each character to the corresponding
  regional indicator symbol."""

  cp_strs = []
  name, ext = os.path.splitext(f)
  for cp in name:
    ncp = 0x1f1e6 - 0x41 + ord(cp)
    cp_strs.append("%04x" % ncp)
  return 'emoji_u%s%s' % ('_'.join(cp_strs), ext)


def copy_with_rename(src_dir, dst_dir, accept_pred=None, rename=None, verbosity=1):
  """Copy files from src_dir to dst_dir that match accept_pred (all if None) and rename
  using rename (if not None), replacing existing files.  accept_pred takes the filename
  and returns True if the file should be copied, rename takes the filename and returns a
  new file name."""

  count = 0
  replace_count = 0
  for src_filename in os.listdir(src_dir):
    if accept_pred and not accept_pred(src_filename):
      continue
    dst_filename = rename(src_filename) if rename else src_filename
    src = os.path.join(src_dir, src_filename)
    dst = os.path.join(dst_dir, dst_filename)
    if os.path.exists(dst):
      if verbosity > 1:
        print "Replacing existing file " + dst
      os.unlink(dst)
      replace_count += 1
    shutil.copy2(src, dst)
    if verbosity > 1:
      print "cp -p %s %s" % (src, dst)
    count += 1
  if verbosity:
    print "Copied/renamed %d files from %s to %s" % (count, src_dir, dst_dir)
  return count, replace_count


def build_svg_dir(dst_dir, clean=False, flags_only=False, verbosity=1):
  """Copies/renames files from noto/color_emoji/svg and then noto/third_party/region-flags/svg,
  giving them the standard format and prefix ('emoji_u' followed by codepoints expressed
  in hex separated by underscore).  If clean, removes the target dir before proceding.
  If flags_only, only does the region-flags."""

  if not os.path.isdir(dst_dir):
    os.makedirs(dst_dir)
  elif clean:
    shutil.rmtree(dst_dir)
    os.makedirs(dst_dir)

  # get files from path relative to noto
  notopath = re.match("^.*/noto/", os.path.realpath(__file__)).group()

  # copy region flags, generating new names based on the tlds.
  flag_dir = os.path.join(notopath, "third_party/region-flags/svg")
  count, replace_count = copy_with_rename(
    flag_dir, dst_dir, accept_pred=_is_svg, rename=_flag_rename, verbosity=verbosity)

  # copy the 'good' svg
  if not flags_only:
    svg_dir = os.path.join(notopath, "color_emoji/svg")
    temp_count, temp_replace_count = copy_with_rename(
      svg_dir, dst_dir, accept_pred=_is_svg_and_startswith_emoji, verbosity=verbosity)
    count += temp_count
    replace_count += temp_replace_count

  if verbosity:
    if replace_count:
      print "Replaced %d existing files" % replace_count
    print "Created %d total files" % (count - replace_count)


def main(argv):
  parser = argparse.ArgumentParser(
      description="Collect svg files into target directory with prefix.")
  parser.add_argument('dst_dir', help="Directory to hold symlinks to files.")
  parser.add_argument('--clean', '-c', help="Replace target directory", action='store_true')
  parser.add_argument('--flags_only', '-fo', help="Only copy region-flags", action='store_true')
  parser.add_argument('--quiet', '-q', dest='v', help="quiet operation.", default=1,
                      action='store_const', const=0)
  parser.add_argument('--verbose', '-v', dest='v', help="verbose operation.",
                      action='store_const', const=2)
  args = parser.parse_args(argv)

  build_svg_dir(args.dst_dir, clean=args.clean, flags_only=args.flags_only, verbosity=args.v)

if __name__ == '__main__':
  main(sys.argv[1:])
