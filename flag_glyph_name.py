#!/usr/bin/env python3
#
# Copyright 2014 Google Inc. All rights reserved.
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

"""Generate a glyph name for flag emojis."""
from __future__ import print_function

__author__ = 'roozbeh@google.com (Roozbeh Pournader)'

import re
import sys

try:
  import add_emoji_gsub
except ImportError as e:
    print(e, file=sys.stderr)
    sys.exit('Python environment is not setup right')

def two_letter_code_to_glyph_name(region_code):
    return 'u%04x_%04x' % (
        add_emoji_gsub.reg_indicator(region_code[0]),
        add_emoji_gsub.reg_indicator(region_code[1]))


subcode_re = re.compile(r'[0-9a-z]{2}-[0-9a-z]+$')
def hyphenated_code_to_glyph_name(sub_code):
  # Hyphenated codes use tag sequences, not regional indicator symbol pairs.
  sub_code = sub_code.lower()
  if not subcode_re.match(sub_code):
    raise Exception('%s is not a valid flag subcode' % sub_code)
  cps = ['u1f3f4']
  cps.extend('e00%02x' % ord(cp) for cp in sub_code if cp != '-')
  cps.append('e007f')
  return '_'.join(cps)


def flag_code_to_glyph_name(flag_code):
  if '-' in flag_code:
    return hyphenated_code_to_glyph_name(flag_code)
  return two_letter_code_to_glyph_name(flag_code)


def main():
    print(' '.join([
        flag_code_to_glyph_name(flag_code) for flag_code in sys.argv[1:]]))

if __name__ == '__main__':
    main()
