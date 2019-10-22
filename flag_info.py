#!/usr/bin/python3
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

"""Quick tool to display count/ids of flag images in a directory named
either using ASCII upper case pairs or the emoji_u+codepoint_sequence
names."""
from __future__ import print_function

import argparse
import re
import glob
import os
from os import path

def _flag_names_from_emoji_file_names(src):
  def _flag_char(char_str):
    return unichr(ord('A') + int(char_str, 16) - 0x1f1e6)
  flag_re = re.compile('emoji_u(1f1[0-9a-f]{2})_(1f1[0-9a-f]{2}).png')
  flags = set()
  for f in glob.glob(path.join(src, 'emoji_u*.png')):
    m = flag_re.match(path.basename(f))
    if not m:
      continue
    flag_short_name = _flag_char(m.group(1)) + _flag_char(m.group(2))
    flags.add(flag_short_name)
  return flags


def _flag_names_from_file_names(src):
  flag_re = re.compile('([A-Z]{2}).png')
  flags = set()
  for f in glob.glob(path.join(src, '*.png')):
    m = flag_re.match(path.basename(f))
    if not m:
      print('no match')
      continue
    flags.add(m.group(1))
  return flags


def _dump_flag_info(names):
  prev = None
  print('%d flags' % len(names))
  for n in sorted(names):
    if n[0] != prev:
      if prev:
        print()
      prev = n[0]
    print(n, end=' ')
  print()


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '-s', '--srcdir', help='location of files', metavar='dir',
      required=True)
  parser.add_argument(
      '-n', '--name_type', help='type of names', metavar='type',
      choices=['ascii', 'codepoint'], required=True)
  args = parser.parse_args()

  if args.name_type == 'ascii':
    names = _flag_names_from_file_names(args.srcdir)
  else:
    names = _flag_names_from_emoji_file_names(args.srcdir)
  print(args.srcdir)
  _dump_flag_info(names)


if __name__ == '__main__':
  main()
