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

"""Modify the Noto Color Emoji font to use GSUB rules for flags and keycaps."""

__author__ = "roozbeh@google.com (Roozbeh Pournader)"

import sys

from fontTools import agl
from fontTools.ttLib.tables import otTables
from fontTools import ttLib
from nototools import font_data


def create_script_list(script_tag='DFLT'):
    """Create a ScriptList for the GSUB table."""
    def_lang_sys = otTables.DefaultLangSys()
    def_lang_sys.ReqFeatureIndex = 0xFFFF
    def_lang_sys.FeatureCount = 1
    def_lang_sys.FeatureIndex = [0]
    def_lang_sys.LookupOrder = None

    script_record = otTables.ScriptRecord()
    script_record.ScriptTag = script_tag
    script_record.Script = otTables.Script()
    script_record.Script.DefaultLangSys = def_lang_sys
    script_record.Script.LangSysCount = 0
    script_record.Script.LangSysRecord = []

    script_list = otTables.ScriptList()
    script_list.ScriptCount = 1
    script_list.ScriptRecord = [script_record]

    return script_list


def create_feature_list(feature_tag, lookup_count):
    """Create a FeatureList for the GSUB table."""
    feature_record = otTables.FeatureRecord()
    feature_record.FeatureTag = feature_tag
    feature_record.Feature = otTables.Feature()
    feature_record.Feature.LookupCount = lookup_count
    feature_record.Feature.LookupListIndex = range(lookup_count)
    feature_record.Feature.FeatureParams = None

    feature_list = otTables.FeatureList()
    feature_list.FeatureCount = 1
    feature_list.FeatureRecord = [feature_record]

    return feature_list


def create_lookup_list(lookups):
    """Create a LookupList for the GSUB table."""
    lookup_list = otTables.LookupList()
    lookup_list.LookupCount = len(lookups)
    lookup_list.Lookup = lookups

    return lookup_list


def get_glyph_name_or_create(char, font):
    """Return the glyph name for a character, creating if it doesn't exist."""
    cmap = font_data.get_cmap(font)
    if char in cmap:
        return cmap[char]

    glyph_name = agl.UV2AGL[char]
    assert glyph_name not in font.glyphOrder

    font['hmtx'].metrics[glyph_name] = [0, 0]
    cmap[char] = glyph_name

    if 'glyf' in font:
        from fontTools.ttLib.tables import _g_l_y_f
        empty_glyph = _g_l_y_f.Glyph()
        font['glyf'].glyphs[glyph_name] = empty_glyph

    font.glyphOrder.append(glyph_name)
    return glyph_name


def create_lookup(table, font, flag=0):
    """Create a Lookup based on mapping table."""
    cmap = font_data.get_cmap(font)

    ligatures = {}
    for output, (ch1, ch2) in table.iteritems():
        output = cmap[output]
        ch1 = get_glyph_name_or_create(ch1, font)
        ch2 = get_glyph_name_or_create(ch2, font)

        ligature = otTables.Ligature()
        ligature.CompCount = 2
        ligature.Component = [ch2]
        ligature.LigGlyph = output

        try:
            ligatures[ch1].append(ligature)
        except KeyError:
            ligatures[ch1] = [ligature]

    ligature_subst = otTables.LigatureSubst()
    ligature_subst.ligatures = ligatures

    lookup = otTables.Lookup()
    lookup.LookupType = 4
    lookup.LookupFlag = flag
    lookup.SubTableCount = 1
    lookup.SubTable = [ligature_subst]

    return lookup


def create_simple_gsub(lookups, script='DFLT', feature='ccmp'):
    """Create a simple GSUB table."""
    gsub_class = ttLib.getTableClass('GSUB')
    gsub = gsub_class('GSUB')

    gsub.table = otTables.GSUB()
    gsub.table.Version = 1.0
    gsub.table.ScriptList = create_script_list(script)
    gsub.table.FeatureList = create_feature_list(feature, len(lookups))
    gsub.table.LookupList = create_lookup_list(lookups)
    return gsub


def reg_indicator(letter):
    """Return a regional indicator character from corresponding capital letter.
    """
    return 0x1F1E6 + ord(letter) - ord('A')


EMOJI_FLAGS = {
    0xFE4E5: (reg_indicator('J'), reg_indicator('P')),  # Japan
    0xFE4E6: (reg_indicator('U'), reg_indicator('S')),  # United States
    0xFE4E7: (reg_indicator('F'), reg_indicator('R')),  # France
    0xFE4E8: (reg_indicator('D'), reg_indicator('E')),  # Germany
    0xFE4E9: (reg_indicator('I'), reg_indicator('T')),  # Italy
    0xFE4EA: (reg_indicator('G'), reg_indicator('B')),  # United Kingdom
    0xFE4EB: (reg_indicator('E'), reg_indicator('S')),  # Spain
    0xFE4EC: (reg_indicator('R'), reg_indicator('U')),  # Russia
    0xFE4ED: (reg_indicator('C'), reg_indicator('N')),  # China
    0xFE4EE: (reg_indicator('K'), reg_indicator('R')),  # Korea
}

KEYCAP = 0x20E3

EMOJI_KEYCAPS = {
    0xFE82C: (ord('#'), KEYCAP),
    0xFE82E: (ord('1'), KEYCAP),
    0xFE82F: (ord('2'), KEYCAP),
    0xFE830: (ord('3'), KEYCAP),
    0xFE831: (ord('4'), KEYCAP),
    0xFE832: (ord('5'), KEYCAP),
    0xFE833: (ord('6'), KEYCAP),
    0xFE834: (ord('7'), KEYCAP),
    0xFE835: (ord('8'), KEYCAP),
    0xFE836: (ord('9'), KEYCAP),
    0xFE837: (ord('0'), KEYCAP),
}

def main(argv):
    """Modify all the fonts given in the command line."""
    for font_name in argv[1:]:
        font = ttLib.TTFont(font_name)

        assert 'GSUB' not in font
        font['GSUB'] = create_simple_gsub([
            create_lookup(EMOJI_KEYCAPS, font),
            create_lookup(EMOJI_FLAGS, font)])

        font_data.delete_from_cmap(
            font, EMOJI_FLAGS.keys() + EMOJI_KEYCAPS.keys())

        font.save(font_name+'-fixed')

if __name__ == '__main__':
    main(sys.argv)
