#!/usr/bin/python
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

__author__ = 'roozbeh@google.com (Roozbeh Pournader)'

import sys

from nototools import add_emoji_gsub

def two_letter_code_to_glyph_name(iso_code):
    return 'u%04x_%04x' % (
        add_emoji_gsub.reg_indicator(iso_code[0]),
        add_emoji_gsub.reg_indicator(iso_code[1]))

def main():
    print ' '.join([
        two_letter_code_to_glyph_name(iso_code) for iso_code in sys.argv[1:]])

if __name__ == '__main__':
    main()
