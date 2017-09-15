#!/usr/bin/env python
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
import shutil
import sys

"""Create aliases in target directory.

The target files should not contain the emoji variation selector
codepoint in their names."""

DATA_ROOT = path.dirname(path.abspath(__file__))

def str_to_seq(seq_str):
  res = [int(s, 16) for s in seq_str.split('_')]
  if 0xfe0f in res:
    print('0xfe0f in file name: %s' % seq_str)
    res = [x for x in res if x != 0xfe0f]
  return tuple(res)


def seq_to_str(seq):
  return '_'.join('%04x' % cp for cp in seq)


def read_default_unknown_flag_aliases():
  unknown_flag_path = path.join(DATA_ROOT, 'unknown_flag_aliases.txt')
  return read_emoji_aliases(unknown_flag_path)


def read_default_emoji_aliases():
  alias_path = path.join(DATA_ROOT, 'emoji_aliases.txt')
  return read_emoji_aliases(alias_path)


def read_emoji_aliases(filename):
  result = {}

  with open(filename, 'r') as f:
    for line in f:
      ix = line.find('#')
      if (ix > -1):
        line = line[:ix]
      line = line.strip()
      if not line:
        continue
      als, trg = (s.strip() for s in line.split(';'))
      try:
        als_seq = tuple([int(x, 16) for x in als.split('_')])
        trg_seq = tuple([int(x, 16) for x in trg.split('_')])
      except:
        print('cannot process alias %s -> %s' % (als, trg))
        continue
      result[als_seq] = trg_seq
  return result


def add_aliases(
    srcdir, dstdir, aliasfile, prefix, ext, replace=False, copy=False,
    dry_run=False):
  """Use aliasfile to create aliases of files in srcdir matching prefix/ext in
  dstdir.  If dstdir is null, use srcdir as dstdir.  If replace is false
  and a file already exists in dstdir, report and do nothing.  If copy is false
  create a symlink, else create a copy.  If dry_run is true, report what would
  be done.  Dstdir will be created if necessary, even if dry_run is true."""

  if not path.isdir(srcdir):
    print('%s is not a directory' % srcdir, file=sys.stderr)
    return

  if not dstdir:
    dstdir = srcdir
  elif not path.isdir(dstdir):
    os.makedirs(dstdir)

  prefix_len = len(prefix)
  suffix_len = len(ext) + 1
  filenames = [path.basename(f)
               for f in glob.glob(path.join(srcdir, '%s*.%s' % (prefix, ext)))]
  seq_to_file = {
      str_to_seq(name[prefix_len:-suffix_len]) : name
      for name in filenames}

  aliases = read_emoji_aliases(aliasfile)
  aliases_to_create = {}
  aliases_to_replace = []
  alias_exists = False
  for als, trg in sorted(aliases.items()):
    if trg not in seq_to_file:
      print('target %s for %s does not exist' % (
          seq_to_str(trg), seq_to_str(als)), file=sys.stderr)
      continue
    alias_name = '%s%s.%s' % (prefix, seq_to_str(als), ext)
    alias_path = path.join(dstdir, alias_name)
    if path.exists(alias_path):
      if replace:
        aliases_to_replace.append(alias_name)
      else:
        print('alias %s exists' % seq_to_str(als), file=sys.stderr)
        alias_exists = True
        continue
    target_file = seq_to_file[trg]
    aliases_to_create[alias_name] = target_file

  if replace:
    if not dry_run:
      for k in sorted(aliases_to_replace):
        os.remove(path.join(dstdir, k))
    print('replacing %d files' % len(aliases_to_replace))
  elif alias_exists:
    print('aborting, aliases exist.', file=sys.stderr)
    return

  for k, v in sorted(aliases_to_create.items()):
    if dry_run:
      msg = 'replace ' if k in aliases_to_replace else ''
      print('%s%s -> %s' % (msg, k, v))
    else:
      try:
        if copy:
          shutil.copy2(path.join(srcdir, v), path.join(dstdir, k))
        else:
          # fix this to create relative symlinks
          if srcdir == dstdir:
            os.symlink(v, path.join(dstdir, k))
          else:
            raise Exception('can\'t create cross-directory symlinks yet')
      except Exception as e:
        print('failed to create %s -> %s' % (k, v), file=sys.stderr)
        raise Exception('oops, ' + str(e))
  print('created %d %s' % (
      len(aliases_to_create), 'copies' if copy else 'symlinks'))


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '-s', '--srcdir', help='directory containing files to alias',
      required=True, metavar='dir')
  parser.add_argument(
      '-d', '--dstdir', help='directory to write aliases, default srcdir',
      metavar='dir')
  parser.add_argument(
      '-a', '--aliasfile', help='alias file (default emoji_aliases.txt)',
      metavar='file', default='emoji_aliases.txt')
  parser.add_argument(
      '-p', '--prefix', help='file name prefix (default emoji_u)',
      metavar='pfx', default='emoji_u')
  parser.add_argument(
      '-e', '--ext', help='file name extension (default png)',
      choices=['ai', 'png', 'svg'], default='png')
  parser.add_argument(
      '-r', '--replace', help='replace existing files/aliases',
      action='store_true')
  parser.add_argument(
      '-c', '--copy', help='create a copy of the file, not a symlink',
      action='store_true')
  parser.add_argument(
      '-n', '--dry_run', help='print out aliases to create only',
      action='store_true')
  args = parser.parse_args()

  add_aliases(
      args.srcdir, args.dstdir, args.aliasfile, args.prefix, args.ext,
      args.replace, args.copy, args.dry_run)


if __name__ == '__main__':
  main()
