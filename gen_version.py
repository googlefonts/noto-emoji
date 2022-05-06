#!/usr/bin/env python3
#
# Copyright 2015 Google Inc. All rights reserved.
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

"""Generate version string for NotoColorEmoji.

This parses the color emoji template file and updates the lines
containing version string info, writing a new file.

The nameID 5 field in the emoji font should reflect the commit/date
of the repo it was built from.  This will build a string of the following
format:
  Version 1.39;GOOG;noto-emoji:20170220:a8a215d2e889'

This is intended to indicate that it was built by Google from noto-emoji
at commit a8a215d2e889 and date 20170220 (since dates are a bit easier
to locate in time than commit hashes).

For building with external data we don't include the commit id as we
might be using different resources.  Instead the version string is:
  Version 1.39;GOOG;noto-emoji:20170518;BETA <msg>

Here the date is the current date, and the message after 'BETA ' is
provided using the '-b' flag.  There's no commit hash.  This also
bypasses some checks about the state of the repo.

The release number should have 2 or 3 minor digits.  Right now we've been
using 2 but at the next major release we probably want to use 3.  This
supports both.  It will bump the version number if none is provided,
maintaining the minor digit length.
"""

import argparse
import datetime
import re

from nototools import tool_utils

# These are not very lenient, we expect to be applied to the noto color
# emoji template ttx file which matches these.  Why then require the
# input argument, you ask?  Um... testing?
_nameid_re = re.compile(r'\s*<namerecord nameID="5"')
_version_re = re.compile(r'\s*Version\s(\d+.\d{2,3})')
_headrev_re = re.compile(r'\s*<fontRevision value="(\d+.\d{2,3})"/>')

def _get_existing_version(lines):
  """Scan lines for all existing version numbers, and ensure they match.
  Return the matched version number string."""

  version = None
  def check_version(new_version):
    if version is not None and new_version != version:
      raise Exception(
          'version %s and namerecord version %s do not match' % (
              version, new_version))
    return new_version

  saw_nameid = False
  for line in lines:
    if saw_nameid:
      saw_nameid = False
      m = _version_re.match(line)
      if not m:
        raise Exception('could not match line "%s" in namerecord' % line)
      version = check_version(m.group(1))
    elif _nameid_re.match(line):
      saw_nameid = True
    else:
      m = _headrev_re.match(line)
      if m:
        version = check_version(m.group(1))
  return version


def _version_to_mm(version):
  majs, mins = version.split('.')
  minor_len = len(mins)
  return int(majs), int(mins), minor_len


def _mm_to_version(major, minor, minor_len):
  fmt = '%%d.%%0%dd' % minor_len
  return fmt % (major, minor)


def _version_compare(lhs, rhs):
  lmaj, lmin, llen = _version_to_mm(lhs)
  rmaj, rmin, rlen = _version_to_mm(rhs)
  # if major versions differ, we don't care about the minor length, else
  # they should be the same
  if lmaj != rmaj:
    return lmaj - rmaj
  if llen != rlen:
    raise Exception('minor version lengths differ: "%s" and "%s"' % (lhs, rhs))
  return lmin - rmin


def _version_bump(version):
  major, minor, minor_len = _version_to_mm(version)
  minor = (minor + 1) % (10 ** minor_len)
  if minor == 0:
    raise Exception('cannot bump version "%s", requires new major' % version)
  return _mm_to_version(major, minor, minor_len)


def _get_repo_version_str(beta):
  """See above for description of this string."""
  if beta is not None:
    date_str = datetime.date.today().strftime('%Y%m%d')
    return 'GOOG;noto-emoji:%s;BETA %s' % (date_str, beta)

  p = tool_utils.resolve_path('[emoji]')
  commit, date, _ = tool_utils.git_head_commit(p)
  if not tool_utils.git_check_remote_commit(p, commit):
    raise Exception('emoji not on upstream master branch')
  date_re = re.compile(r'(\d{4})-(\d{2})-(\d{2})')
  m = date_re.match(date)
  if not m:
    raise Exception('could not match "%s" with "%s"' % (date, date_re.pattern))
  ymd = ''.join(m.groups())
  return 'GOOG;noto-emoji:%s:%s' % (ymd, commit[:12])


def _replace_existing_version(lines, version, version_str):
  """Update lines with new version strings in appropriate places."""
  saw_nameid = False
  for i in range(len(lines)):
    line = lines[i]
    if saw_nameid:
      saw_nameid = False
      # preserve indentation
      lead_ws = len(line) - len(line.lstrip())
      lines[i] = line[:lead_ws] + version_str + '\n'
    elif _nameid_re.match(line):
      saw_nameid = True
    elif _headrev_re.match(line):
      lead_ws = len(line) - len(line.lstrip())
      lines[i] = line[:lead_ws] + '<fontRevision value="%s"/>\n' % version


def update_version(srcfile, dstfile, version, beta):
  """Update version in srcfile and write to dstfile.  If version is None,
  bumps the current version, else version must be greater than the
  current version."""

  with open(srcfile, 'r') as f:
    lines = f.readlines()
  current_version = _get_existing_version(lines)
  if not version:
    version = _version_bump(current_version)
  elif version and _version_compare(version, current_version) <= 0:
    raise Exception('new version %s is <= current version %s' % (
        version, current_version))
  version_str = 'Version %s;%s' % (version, _get_repo_version_str(beta))
  _replace_existing_version(lines, version, version_str)
  with open(dstfile, 'w') as f:
    for line in lines:
      f.write(line)


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '-v', '--version', help='version number, default bumps the current '
      'version', metavar='ver')
  parser.add_argument(
      '-s', '--src', help='ttx file with name and head tables',
      metavar='file', required=True)
  parser.add_argument(
      '-d', '--dst', help='name of edited ttx file to write',
      metavar='file', required=True)
  parser.add_argument(
      '-b', '--beta', help='beta tag if font is built using external resources')
  args = parser.parse_args()

  update_version(args.src, args.dst, args.version, args.beta)


if __name__ == '__main__':
  main()
