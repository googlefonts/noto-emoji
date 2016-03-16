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

"""Compare emoji image file namings against unicode property data."""

import argparse
import collections
import glob
from os import path
import re
import sys

from nototools import unicode_data

def _is_regional_indicator(cp):
  return 0x1f1e6 <= cp <= 0x1f1ff


def _is_skintone_modifier(cp):
  return 0x1f3fb <= cp <= 0x1f3ff


def _seq_string(seq):
  return '_'.join('%04x' % cp for cp in seq)


def _check_valid_emoji(sorted_seqs):
  """Ensure all emoji are either valid emoji or specific chars."""

  valid_cps = set(unicode_data.get_emoji() | unicode_data.proposed_emoji_cps())
  valid_cps.add(0x200d)  # ZWJ
  valid_cps.add(0x20e3)  # combining enclosing keycap
  valid_cps.add(0xfe0f)  # variation selector (emoji presentation)
  valid_cps.add(0xfe82b)  # PUA value for unknown flag

  not_emoji = set()
  for seq in sorted_seqs:
    for cp in seq:
      if cp not in valid_cps:
        not_emoji.add(cp)

  if len(not_emoji):
    print >> sys.stderr, '%d non-emoji found:' % len(not_emoji)
    for cp in sorted(not_emoji):
      print >> sys.stderr, '%04X' % cp


def _check_zwj(sorted_seqs):
  """Ensure zwj is only between two appropriate emoji."""
  ZWJ = 0x200D
  EMOJI_PRESENTATION_VS = 0xFE0F

  for seq in sorted_seqs:
    if ZWJ not in seq:
      continue
    if seq[0] == 0x200d:
      print >> sys.stderr, 'zwj at head of sequence'
    if len(seq) == 1:
      continue
    if seq[-1] == 0x200d:
      print >> sys.stderr, 'zwj at end of sequence'
    for i, cp in enumerate(seq):
      if cp == ZWJ:
        pcp = seq[i-1]
        if pcp != EMOJI_PRESENTATION_VS and not unicode_data.is_emoji(pcp):
          print >> sys.stderr, 'non-emoji %04X preceeds ZWJ' % pcp
        fcp = seq[i+1]
        if not unicode_data.is_emoji(fcp):
          print >> sys.stderr, 'non-emoji %04X follows ZWJ' % fcp


def _check_flags(sorted_seqs):
  """Ensure regional indicators are only in sequences of one or two, and
  never mixed."""
  for seq in sorted_seqs:
    have_reg = None
    for cp in seq:
      is_reg = _is_regional_indicator(cp)
      if have_reg == None:
        have_reg = is_reg
      elif have_reg != is_reg:
        print >> sys.stderr, ('mix of regional and non-regional in %s' %
            _seq_string(seq))
    if have_reg and len(seq) > 2:
      # We provide dummy glyphs for regional indicators, so there are sequences
      # with single regional indicator symbols.
      print >> sys.stderr, ('regional indicator sequence length != 2: %s' %
            _seq_string(seq))


def _check_skintone(sorted_seqs):
  """Ensure skin tone modifiers are not applied to emoji that are not defined
  to take them.  May appear standalone, though.  Also check that emoji that take
  skin tone modifiers have a complete set."""
  base_to_modifiers = collections.defaultdict(set)
  for seq in sorted_seqs:
    for i, cp in enumerate(seq):
      if _is_skintone_modifier(cp):
        if i == 0:
          if len(seq) > 1:
            print >> sys.stderr, 'skin color selector first in sequence %s'
          # standalone are ok
          continue
        pcp = seq[i-1]
        if not unicode_data.is_emoji_modifier_base(pcp):
          print >> sys.stderr, (
              'emoji skintone modifier applied to non-base at %d: %s' % (
                  i, _seq_string(seq)))
      elif unicode_data.is_emoji_modifier_base(cp):
        if i < len(seq) - 1 and _is_skintone_modifier(seq[i+1]):
          base_to_modifiers[cp].add(seq[i+1])
        elif cp not in base_to_modifiers:
          base_to_modifiers[cp] = set()
  for cp, modifiers in sorted(base_to_modifiers.iteritems()):
    if len(modifiers) != 5:
      print 'emoji base %04X has %d modifiers defined (%s)' % (
          cp, len(modifiers),
          ', '.join('%04x' % cp for cp in sorted(modifiers)))

def check_sequences(seqs):
  sorted_seqs = sorted(seqs)
  _check_valid_emoji(sorted_seqs)
  _check_zwj(sorted_seqs)
  _check_flags(sorted_seqs)
  _check_skintone(sorted_seqs)


def _collect_sequences(dirs, prefix='emoji_u'):
  seqs = set()
  path_re = re.compile('%s([a-zA-Z0-9_]+)\.png' % prefix)
  for d in dirs:
    for f in glob.glob(path.join(d, '%s*.png' % prefix)):
      m = path_re.match(path.basename(f))
      if not m:
        print >> sys.stderr, 'could not match file "%s"' % f
        continue
      seq = tuple(int(s, 16) for s in m.group(1).split('_'))
      if seq in seqs:
        print >> sys.stderr, 'duplicate sequence for "%s"' % f
        continue
      seqs.add(seq)
  return seqs


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '-d', '--dirs', help='directories containing emoji images',
      metavar='dir', nargs='+', required=True)
  args = parser.parse_args()
  check_sequences(_collect_sequences(args.dirs))


if __name__ == '__main__':
  main()
