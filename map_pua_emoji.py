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

"""Modify an emoji font to map legacy PUA characters to standard ligatures."""

__author__ = 'roozbeh@google.com (Roozbeh Pournader)'

import sys
import itertools

from fontTools import ttLib

from nototools import font_data

import add_emoji_gsub


def get_glyph_name_from_gsub(char_seq, font):
    """Find the glyph name for ligature of a given character sequence from GSUB.
    """
    cmap = font_data.get_cmap(font)
    # FIXME: So many assumptions are made here.
    try:
        first_glyph = cmap[char_seq[0]]
        rest_of_glyphs = [cmap[ch] for ch in char_seq[1:]]
    except KeyError:
        return None

    for lookup in font['GSUB'].table.LookupList.Lookup:
        ligatures = lookup.SubTable[0].ligatures
        try:
            for ligature in ligatures[first_glyph]:
                if ligature.Component == rest_of_glyphs:
                    return ligature.LigGlyph
        except KeyError:
            continue
    return None


def add_pua_cmap_to_font(font):
    cmap = font_data.get_cmap(font)
    for pua, (ch1, ch2) in itertools.chain(
        add_emoji_gsub.EMOJI_KEYCAPS.items(), add_emoji_gsub.EMOJI_FLAGS.items()
    ):
        if pua not in cmap:
            glyph_name = get_glyph_name_from_gsub([ch1, ch2], font)
            if glyph_name is not None:
                cmap[pua] = glyph_name


def add_pua_cmap(source_file, target_file):
    """Add PUA characters to the cmap of the first font and save as second."""
    font = ttLib.TTFont(source_file)
    add_pua_cmap_to_font(font)
    font.save(target_file)


def main(argv):
    """Save the first font given to the second font."""
    add_pua_cmap(argv[1], argv[2])


if __name__ == '__main__':
    main(sys.argv)

