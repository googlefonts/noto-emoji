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
from __future__ import print_function

import argparse
import collections
import glob
import os
from os import path
import re
import sys

from nototools import unicode_data
import add_aliases

ZWJ = 0x200d
EMOJI_VS = 0xfe0f

END_TAG = 0xe007f

def _make_tag_set():
  tag_set = set()
  tag_set |= set(range(0xe0030, 0xe003a))  # 0-9
  tag_set |= set(range(0xe0061, 0xe007b))  # a-z
  tag_set.add(END_TAG)
  return tag_set

TAG_SET = _make_tag_set()

_namedata = None

def seq_name(seq):
  global _namedata

  if not _namedata:
    def strip_vs_map(seq_map):
      return {
          unicode_data.strip_emoji_vs(k): v
          for k, v in seq_map.iteritems()}
    _namedata = [
        strip_vs_map(unicode_data.get_emoji_combining_sequences()),
        strip_vs_map(unicode_data.get_emoji_flag_sequences()),
        strip_vs_map(unicode_data.get_emoji_modifier_sequences()),
        strip_vs_map(unicode_data.get_emoji_zwj_sequences()),
        ]

  if len(seq) == 1:
    return unicode_data.name(seq[0], None)

  for data in _namedata:
    if seq in data:
      return data[seq]
  if EMOJI_VS in seq:
    non_vs_seq = unicode_data.strip_emoji_vs(seq)
    for data in _namedata:
      if non_vs_seq in data:
        return data[non_vs_seq]

  return None


def _check_no_vs(sorted_seq_to_filepath):
  """Our image data does not use emoji presentation variation selectors."""
  for seq, fp in sorted_seq_to_filepath.iteritems():
    if EMOJI_VS in seq:
      print('check no VS: FE0F in path: %s' % fp)


def _check_valid_emoji_cps(sorted_seq_to_filepath, unicode_version):
  """Ensure all cps in these sequences are valid emoji cps or specific cps
  used in forming emoji sequences.  This is a 'pre-check' that reports
  this specific problem."""

  valid_cps = set(unicode_data.get_emoji())
  if unicode_version is None or unicode_version >= unicode_data.PROPOSED_EMOJI_AGE:
    valid_cps |= unicode_data.proposed_emoji_cps()
  else:
    valid_cps = set(
        cp for cp in valid_cps if unicode_data.age(cp) <= unicode_version)
  valid_cps.add(0x200d)  # ZWJ
  valid_cps.add(0x20e3)  # combining enclosing keycap
  valid_cps.add(0xfe0f)  # variation selector (emoji presentation)
  valid_cps.add(0xfe82b)  # PUA value for unknown flag
  valid_cps |= TAG_SET  # used in subregion tag sequences

  not_emoji = {}
  for seq, fp in sorted_seq_to_filepath.iteritems():
    for cp in seq:
      if cp not in valid_cps:
        if cp not in not_emoji:
          not_emoji[cp] = []
        not_emoji[cp].append(fp)

  if len(not_emoji):
    print(
        'check valid emoji cps: %d non-emoji cp found' % len(not_emoji),
        file=sys.stderr)
    for cp in sorted(not_emoji):
      fps = not_emoji[cp]
      print(
          'check valid emoji cps: %04x (in %d sequences)' % (cp, len(fps)),
          file=sys.stderr)


def _check_zwj(sorted_seq_to_filepath):
  """Ensure zwj is only between two appropriate emoji.  This is a 'pre-check'
  that reports this specific problem."""

  for seq, fp in sorted_seq_to_filepath.iteritems():
    if ZWJ not in seq:
      continue
    if seq[0] == ZWJ:
      print('check zwj: zwj at head of sequence in %s' % fp, file=sys.stderr)
    if len(seq) == 1:
      continue
    if seq[-1] == ZWJ:
      print('check zwj: zwj at end of sequence in %s' % fp, file=sys.stderr)
    for i, cp in enumerate(seq):
      if cp == ZWJ:
        if i > 0:
          pcp = seq[i-1]
          if pcp != EMOJI_VS and not unicode_data.is_emoji(pcp):
            print(
                'check zwj: non-emoji %04x preceeds ZWJ in %s' % (pcp, fp),
                file=sys.stderr)
        if i < len(seq) - 1:
          fcp = seq[i+1]
          if not unicode_data.is_emoji(fcp):
            print(
                'check zwj: non-emoji %04x follows ZWJ in %s' % (fcp, fp),
                file=sys.stderr)


def _check_flags(sorted_seq_to_filepath):
  """Ensure regional indicators are only in sequences of one or two, and
  never mixed."""
  for seq, fp in sorted_seq_to_filepath.iteritems():
    have_reg = None
    for cp in seq:
      is_reg = unicode_data.is_regional_indicator(cp)
      if have_reg == None:
        have_reg = is_reg
      elif have_reg != is_reg:
        print(
            'check flags: mix of regional and non-regional in %s' % fp,
            file=sys.stderr)
    if have_reg and len(seq) > 2:
      # We provide dummy glyphs for regional indicators, so there are sequences
      # with single regional indicator symbols, the len check handles this.
      print(
          'check flags: regional indicator sequence length != 2 in %s' % fp,
          file=sys.stderr)

def _check_tags(sorted_seq_to_filepath):
  """Ensure tag sequences (for subregion flags) conform to the spec.  We don't
  validate against CLDR, just that there's a sequence of 2 or more tags starting
  and ending with the appropriate codepoints."""

  BLACK_FLAG = 0x1f3f4
  BLACK_FLAG_SET = set([BLACK_FLAG])
  for seq, fp in sorted_seq_to_filepath.iteritems():
    seq_set = set(cp for cp in seq)
    overlap_set = seq_set & TAG_SET
    if not overlap_set:
      continue
    if seq[0] != BLACK_FLAG:
      print('check tags: bad start tag in %s' % fp)
    elif seq[-1] != END_TAG:
      print('check tags: bad end tag in %s' % fp)
    elif len(seq) < 4:
      print('check tags: sequence too short in %s' % fp)
    elif seq_set - TAG_SET != BLACK_FLAG_SET:
      print('check tags: non-tag items in %s' % fp)


def _check_skintone(sorted_seq_to_filepath):
  """Ensure skin tone modifiers are not applied to emoji that are not defined
  to take them.  May appear standalone, though.  Also check that emoji that take
  skin tone modifiers have a complete set."""
  base_to_modifiers = collections.defaultdict(set)
  for seq, fp in sorted_seq_to_filepath.iteritems():
    for i, cp in enumerate(seq):
      if unicode_data.is_skintone_modifier(cp):
        if i == 0:
          if len(seq) > 1:
            print(
                'check skintone: skin color selector first in sequence %s' % fp,
                file=sys.stderr)
          # standalone are ok
          continue
        pcp = seq[i-1]
        if not unicode_data.is_emoji_modifier_base(pcp):
          print(
              'check skintone: emoji skintone modifier applied to non-base ' +
              'at %d: %s' % (i, fp), file=sys.stderr)
        else:
          if pcp not in base_to_modifiers:
            base_to_modifiers[pcp] = set()
          base_to_modifiers[pcp].add(cp)

  for cp, modifiers in sorted(base_to_modifiers.iteritems()):
    if len(modifiers) != 5:
      print(
          'check skintone: base %04x has %d modifiers defined (%s) in %s' % (
              cp, len(modifiers),
              ', '.join('%04x' % cp for cp in sorted(modifiers)), fp),
          file=sys.stderr)


def _check_zwj_sequences(sorted_seq_to_filepath, unicode_version):
  """Verify that zwj sequences are valid for the given unicode version."""
  for seq, fp in sorted_seq_to_filepath.iteritems():
    if ZWJ not in seq:
      continue
    age = unicode_data.get_emoji_sequence_age(seq)
    if age is None or unicode_version is not None and age > unicode_version:
      print('check zwj sequences: undefined sequence %s' % fp)


def _check_no_alias_sources(sorted_seq_to_filepath):
  """Check that we don't have sequences that we expect to be aliased to
  some other sequence."""
  aliases = add_aliases.read_default_emoji_aliases()
  for seq, fp in sorted_seq_to_filepath.iteritems():
    if seq in aliases:
      print('check no alias sources: aliased sequence %s' % fp)


def _check_coverage(seq_to_filepath, unicode_version):
  """Ensure we have all and only the cps and sequences that we need for the
  font as of this version."""

  age = unicode_version

  non_vs_to_canonical = {}
  for k in seq_to_filepath:
    if EMOJI_VS in k:
      non_vs = unicode_data.strip_emoji_vs(k)
      non_vs_to_canonical[non_vs] = k

  aliases = add_aliases.read_default_emoji_aliases()
  for k, v in sorted(aliases.items()):
    if v not in seq_to_filepath and v not in non_vs_to_canonical:
      alias_str = unicode_data.seq_to_string(k)
      target_str = unicode_data.seq_to_string(v)
      print('coverage: alias %s missing target %s' % (alias_str, target_str))
      continue
    if k in seq_to_filepath or k in non_vs_to_canonical:
      alias_str = unicode_data.seq_to_string(k)
      target_str = unicode_data.seq_to_string(v)
      print('coverage: alias %s already exists as %s (%s)' % (
          alias_str, target_str, seq_name(v)))
      continue
    filename = seq_to_filepath.get(v) or seq_to_filepath[non_vs_to_canonical[v]]
    seq_to_filepath[k] = 'alias:' + filename

  # check single emoji, this includes most of the special chars
  emoji = sorted(unicode_data.get_emoji(age=age))
  for cp in emoji:
    if tuple([cp]) not in seq_to_filepath:
      print(
          'coverage: missing single %04x (%s)' % (
              cp, unicode_data.name(cp, '<no name>')))

  # special characters
  # all but combining enclosing keycap are currently marked as emoji
  for cp in [ord('*'), ord('#'), ord(u'\u20e3')] + range(0x30, 0x3a):
    if cp not in emoji and tuple([cp]) not in seq_to_filepath:
      print('coverage: missing special %04x (%s)' % (cp, unicode_data.name(cp)))

  # combining sequences
  comb_seq_to_name = sorted(
      unicode_data.get_emoji_combining_sequences(age=age).iteritems())
  for seq, name in comb_seq_to_name:
    if seq not in seq_to_filepath:
      # strip vs and try again
      non_vs_seq = unicode_data.strip_emoji_vs(seq)
      if non_vs_seq not in seq_to_filepath:
        print('coverage: missing combining sequence %s (%s)' %
              (unicode_data.seq_to_string(seq), name))

  # flag sequences
  flag_seq_to_name = sorted(
      unicode_data.get_emoji_flag_sequences(age=age).iteritems())
  for seq, name in flag_seq_to_name:
    if seq not in seq_to_filepath:
      print('coverage: missing flag sequence %s (%s)' %
            (unicode_data.seq_to_string(seq), name))

  # skin tone modifier sequences
  mod_seq_to_name = sorted(
      unicode_data.get_emoji_modifier_sequences(age=age).iteritems())
  for seq, name in mod_seq_to_name:
    if seq not in seq_to_filepath:
      print('coverage: missing modifier sequence %s (%s)' % (
          unicode_data.seq_to_string(seq), name))

  # zwj sequences
  # some of ours include the emoji presentation variation selector and some
  # don't, and the same is true for the canonical sequences.  normalize all
  # of them to omit it to test coverage, but report the canonical sequence.
  zwj_seq_without_vs = set()
  for seq in seq_to_filepath:
    if ZWJ not in seq:
      continue
    if EMOJI_VS in seq:
      seq = tuple(cp for cp in seq if cp != EMOJI_VS)
    zwj_seq_without_vs.add(seq)

  for seq, name in sorted(
      unicode_data.get_emoji_zwj_sequences(age=age).iteritems()):
    if EMOJI_VS in seq:
      test_seq = tuple(s for s in seq if s != EMOJI_VS)
    else:
      test_seq = seq
    if test_seq not in zwj_seq_without_vs:
      print('coverage: missing (canonical) zwj sequence %s (%s)' % (
          unicode_data.seq_to_string(seq), name))

  # check for 'unknown flag'
  # this is either emoji_ufe82b or 'unknown_flag', but we filter out things that
  # don't start with our prefix so 'unknown_flag' would be excluded by default.
  if tuple([0xfe82b]) not in seq_to_filepath:
    print('coverage: missing unknown flag PUA fe82b')


def check_sequence_to_filepath(seq_to_filepath, unicode_version, coverage):
  sorted_seq_to_filepath = collections.OrderedDict(
      sorted(seq_to_filepath.items()))
  _check_no_vs(sorted_seq_to_filepath)
  _check_valid_emoji_cps(sorted_seq_to_filepath, unicode_version)
  _check_zwj(sorted_seq_to_filepath)
  _check_flags(sorted_seq_to_filepath)
  _check_tags(sorted_seq_to_filepath)
  _check_skintone(sorted_seq_to_filepath)
  _check_zwj_sequences(sorted_seq_to_filepath, unicode_version)
  _check_no_alias_sources(sorted_seq_to_filepath)
  if coverage:
    _check_coverage(sorted_seq_to_filepath, unicode_version)


def create_sequence_to_filepath(name_to_dirpath, prefix, suffix):
  """Check names, and convert name to sequences for names that are ok,
  returning a sequence to file path mapping.  Reports bad segments
  of a name to stderr."""
  segment_re = re.compile(r'^[0-9a-f]{4,6}$')
  result = {}
  for name, dirname in name_to_dirpath.iteritems():
    if not name.startswith(prefix):
      print('expected prefix "%s" for "%s"' % (prefix, name))
      continue

    segments = name[len(prefix): -len(suffix)].split('_')
    segfail = False
    seq = []
    for s in segments:
      if not segment_re.match(s):
        print('bad codepoint name "%s" in %s/%s' % (s, dirname, name))
        segfail = True
        continue
      n = int(s, 16)
      if n > 0x10ffff:
        print('codepoint "%s" out of range in %s/%s' % (s, dirname, name))
        segfail = True
        continue
      seq.append(n)
    if not segfail:
      result[tuple(seq)] = path.join(dirname, name)
  return result


def collect_name_to_dirpath(directory, prefix, suffix, exclude=None):
  """Return a mapping from filename to path rooted at directory, ignoring files
  that don't match suffix, and subtrees with names in exclude.  Report when a
  filename appears in more than one subdir; the first path found is kept."""
  result = {}
  for dirname, dirs, files in os.walk(directory, topdown=True):
    if exclude:
      dirs[:] = [d for d in dirs if d not in exclude]

    if directory != '.':
      dirname = path.join(directory, dirname)
    for f in files:
      if not f.endswith(suffix):
        continue
      if f in result:
        print('duplicate file "%s" in %s and %s ' % (
            f, dirname, result[f]), file=sys.stderr)
        continue
      result[f] = dirname
  return result


def collect_name_to_dirpath_with_override(dirs, prefix, suffix, exclude=None):
  """Return a mapping from filename to a directory path rooted at a directory
  in dirs, using collect_name_to_filepath.  The last directory is retained. This
  does not report an error if a file appears under more than one root directory,
  so lets later root directories override earlier ones.  Use 'exclude' to
  name subdirectories (of any root) whose subtree you wish to skip."""
  result = {}
  for d in dirs:
    result.update(collect_name_to_dirpath(d, prefix, suffix, exclude))
  return result


def run_check(dirs, prefix, suffix, exclude, unicode_version, coverage):
  msg = ''
  if unicode_version:
    msg = ' (%3.1f)' % unicode_version
  print('Checking files with prefix "%s" and suffix "%s"%s in:\n  %s' % (
      prefix, suffix, msg, '\n  '.join(dirs)))
  name_to_dirpath = collect_name_to_dirpath_with_override(
      dirs, prefix=prefix, suffix=suffix, exclude=exclude)
  print('checking %d names' % len(name_to_dirpath))
  seq_to_filepath = create_sequence_to_filepath(name_to_dirpath, prefix, suffix)
  print('checking %d sequences' % len(seq_to_filepath))
  check_sequence_to_filepath(seq_to_filepath, unicode_version, coverage)
  print('done.')


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '-d', '--dirs', help='directory roots containing emoji images',
      metavar='dir', nargs='+', required=True)
  parser.add_argument(
      '-e', '--exclude', help='names of source subdirs to exclude',
      metavar='dir', nargs='+')
  parser.add_argument(
      '-c', '--coverage', help='test for complete coverage',
      action='store_true')
  parser.add_argument(
      '-p', '--prefix', help='prefix to match, default "emoji_u"',
      metavar='pfx', default='emoji_u')
  parser.add_argument(
      '-s', '--suffix', help='suffix to match, default ".png"', metavar='sfx',
      default='.png')
  parser.add_argument(
      '-u', '--unicode_version', help='limit to this unicode version or before',
      metavar='version', type=float)
  args = parser.parse_args()
  run_check(
      args.dirs, args.prefix, args.suffix, args.exclude, args.unicode_version,
      args.coverage)


if __name__ == '__main__':
  main()
