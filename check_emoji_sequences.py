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

"""Compare emoji image file namings against unicode property data."""

import argparse
import collections
import glob
import os
from os import path
import re
import sys

from nototools import unicode_data

ZWJ = 0x200d
EMOJI_VS = 0xfe0f

def _is_regional_indicator(cp):
  return 0x1f1e6 <= cp <= 0x1f1ff


def _is_skintone_modifier(cp):
  return 0x1f3fb <= cp <= 0x1f3ff


def _seq_string(seq):
  return '_'.join('%04x' % cp for cp in seq)


def _check_valid_emoji(sorted_seq_to_filepath):
  """Ensure all emoji are either valid emoji or specific chars."""

  valid_cps = set(unicode_data.get_emoji() | unicode_data.proposed_emoji_cps())
  valid_cps.add(0x200d)  # ZWJ
  valid_cps.add(0x20e3)  # combining enclosing keycap
  valid_cps.add(0xfe0f)  # variation selector (emoji presentation)
  valid_cps.add(0xfe82b)  # PUA value for unknown flag

  not_emoji = {}
  for seq, fp in sorted_seq_to_filepath.iteritems():
    for cp in seq:
      if cp not in valid_cps:
        if cp not in not_emoji:
          not_emoji[cp] = []
        not_emoji[cp].append(fp)

  if len(not_emoji):
    print >> sys.stderr, '%d non-emoji found:' % len(not_emoji)
    for cp in sorted(not_emoji):
      print >> sys.stderr, '%04x (in %s)' % (cp, ', '.join(not_emoji[cp]))


def _check_zwj(sorted_seq_to_filepath):
  """Ensure zwj is only between two appropriate emoji."""
  ZWJ = 0x200D
  EMOJI_PRESENTATION_VS = 0xFE0F

  for seq, fp in sorted_seq_to_filepath.iteritems():
    if ZWJ not in seq:
      continue
    if seq[0] == 0x200d:
      print >> sys.stderr, 'zwj at head of sequence in %s' % fp
    if len(seq) == 1:
      continue
    if seq[-1] == 0x200d:
      print >> sys.stderr, 'zwj at end of sequence in %s' % fp
    for i, cp in enumerate(seq):
      if cp == ZWJ:
        if i > 0:
          pcp = seq[i-1]
          if pcp != EMOJI_PRESENTATION_VS and not unicode_data.is_emoji(pcp):
            print >> sys.stderr, 'non-emoji %04x preceeds ZWJ in %s' % (pcp, fp)
        if i < len(seq) - 1:
          fcp = seq[i+1]
          if not unicode_data.is_emoji(fcp):
            print >> sys.stderr, 'non-emoji %04x follows ZWJ in %s' % (fcp, fp)


def _check_flags(sorted_seq_to_filepath):
  """Ensure regional indicators are only in sequences of one or two, and
  never mixed."""
  for seq, fp in sorted_seq_to_filepath.iteritems():
    have_reg = None
    for cp in seq:
      is_reg = _is_regional_indicator(cp)
      if have_reg == None:
        have_reg = is_reg
      elif have_reg != is_reg:
        print >> sys.stderr, 'mix of regional and non-regional in %s' % fp
    if have_reg and len(seq) > 2:
      # We provide dummy glyphs for regional indicators, so there are sequences
      # with single regional indicator symbols.
      print >> sys.stderr, 'regional indicator sequence length != 2 in %s' % fp


def _check_skintone(sorted_seq_to_filepath):
  """Ensure skin tone modifiers are not applied to emoji that are not defined
  to take them.  May appear standalone, though.  Also check that emoji that take
  skin tone modifiers have a complete set."""
  base_to_modifiers = collections.defaultdict(set)
  for seq, fp in sorted_seq_to_filepath.iteritems():
    for i, cp in enumerate(seq):
      if _is_skintone_modifier(cp):
        if i == 0:
          if len(seq) > 1:
            print >> sys.stderr, 'skin color selector first in sequence %s' % fp
          # standalone are ok
          continue
        pcp = seq[i-1]
        if not unicode_data.is_emoji_modifier_base(pcp):
          print >> sys.stderr, (
              'emoji skintone modifier applied to non-base at %d: %s' % (i, fp))
      elif unicode_data.is_emoji_modifier_base(cp):
        if i < len(seq) - 1 and _is_skintone_modifier(seq[i+1]):
          base_to_modifiers[cp].add(seq[i+1])
        elif cp not in base_to_modifiers:
          base_to_modifiers[cp] = set()
  for cp, modifiers in sorted(base_to_modifiers.iteritems()):
    if len(modifiers) != 5:
      print >> sys.stderr, 'emoji base %04x has %d modifiers defined (%s) in %s' % (
          cp, len(modifiers),
          ', '.join('%04x' % cp for cp in sorted(modifiers)), fp)


def _check_zwj_sequences(seq_to_filepath):
  """Verify that zwj sequences are valid."""
  zwj_sequence_to_type = unicode_data.get_emoji_zwj_sequences()
  # strip emoji variant selectors and add these back in
  zwj_sequence_without_vs_to_type_canonical = {}
  for seq, seq_type in zwj_sequence_to_type.iteritems():
    if EMOJI_VS in seq:
      stripped_seq = tuple(s for s in seq if s != EMOJI_VS)
      zwj_sequence_without_vs_to_type_canonical[stripped_seq] = (seq_type, seq)

  zwj_seq_to_filepath = {
      seq: fp for seq, fp in seq_to_filepath.iteritems()
      if ZWJ in seq}

  for seq, fp in zwj_seq_to_filepath.iteritems():
    if seq not in zwj_sequence_to_type:
      if seq not in zwj_sequence_without_vs_to_type_canonical:
        print >> sys.stderr, 'zwj sequence not defined: %s' % fp
      else:
        _, can = zwj_sequence_without_vs_to_type_canonical[seq]
        print >> sys.stderr, 'canonical sequence %s contains vs: %s' % (
            _seq_string(can), fp)

  # check that all zwj sequences are covered
  for seq in zwj_seq_to_filepath:
    if seq in zwj_sequence_to_type:
      del zwj_sequence_to_type[seq]
    elif seq in zwj_sequence_without_vs_to_type_canonical:
      canon_seq = zwj_sequence_without_vs_to_type_canonical[seq][1]
      del zwj_sequence_to_type[canon_seq]
  if zwj_sequence_to_type:
    print >> sys.stderr, 'missing %d zwj sequences' % len(zwj_sequence_to_type)
    for seq, seq_type in sorted(zwj_sequence_to_type.items()):
      print >> sys.stderr, '  %s: %s' % (_seq_string(seq), seq_type)


def check_sequence_to_filepath(seq_to_filepath):
  sorted_seq_to_filepath = collections.OrderedDict(
      sorted(seq_to_filepath.items()))
  _check_valid_emoji(sorted_seq_to_filepath)
  _check_zwj(sorted_seq_to_filepath)
  _check_flags(sorted_seq_to_filepath)
  _check_skintone(sorted_seq_to_filepath)
  _check_zwj_sequences(sorted_seq_to_filepath)


def create_sequence_to_filepath(name_to_dirpath, prefix, suffix):
  """Check names, and convert name to sequences for names that are ok,
  returning a sequence to file path mapping.  Reports bad segments
  of a name to stderr."""
  segment_re = re.compile(r'^[0-9a-f]{4,6}$')
  result = {}
  for name, dirname in name_to_dirpath.iteritems():
    if not name.startswith(prefix):
      print 'expected prefix "%s" for "%s"' % (prefix, name)
      continue

    segments = name[len(prefix): -len(suffix)].split('_')
    segfail = False
    seq = []
    for s in segments:
      if not segment_re.match(s):
        print 'bad codepoint name "%s" in %s/%s' % (s, dirname, name)
        segfail = True
        continue
      n = int(s, 16)
      if n > 0x10ffff:
        print 'codepoint "%s" out of range in %s/%s' % (s, dirname, name)
        segfail = True
        continue
      seq.append(n)
    if not segfail:
      result[tuple(seq)] = path.join(dirname, name)
  return result


def collect_name_to_dirpath(directory, prefix, suffix):
  """Return a mapping from filename to path rooted at directory, ignoring files
  that don't match suffix.  Report when a filename appears in more than one
  subdir; the first path found is kept."""
  result = {}
  for dirname, _, files in os.walk(directory):
    if directory != '.':
      dirname = path.join(directory, dirname)
    for f in files:
      if not f.endswith(suffix):
        continue
      if f in result:
        print >> sys.stderr, 'duplicate file "%s" in %s and %s ' % (
            f, dirname, result[f])
        continue
      result[f] = dirname
  return result


def collect_name_to_dirpath_with_override(dirs, prefix, suffix):
  """Return a mapping from filename to a directory path rooted at a directory
  in dirs, using collect_name_to_filepath.  The last directory is retained. This
  does not report an error if a file appears under more than one root directory,
  so lets later root directories override earlier ones."""
  result = {}
  for d in dirs:
    result.update(collect_name_to_dirpath(d, prefix, suffix))
  return result


def run_check(dirs, prefix, suffix):
  print 'Checking files with prefix "%s" and suffix "%s" in:\n  %s' % (
      prefix, suffix, '\n  '.join(dirs))
  name_to_dirpath = collect_name_to_dirpath_with_override(
      dirs, prefix=prefix, suffix=suffix)
  print 'checking %d names' % len(name_to_dirpath)
  seq_to_filepath = create_sequence_to_filepath(name_to_dirpath, prefix, suffix)
  print 'checking %d sequences' % len(seq_to_filepath)
  check_sequence_to_filepath(seq_to_filepath)
  print 'done.'


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '-d', '--dirs', help='directories containing emoji images',
      metavar='dir', nargs='+', required=True)
  parser.add_argument(
      '-p', '--prefix', help='prefix to match, default "emoji_u"',
      metavar='pfx', default='emoji_u')
  parser.add_argument(
      '-s', '--suffix', help='suffix to match, default ".png"', metavar='sfx',
      default='.png')
  args = parser.parse_args()
  run_check(args.dirs, args.prefix, args.suffix)


if __name__ == '__main__':
  main()
