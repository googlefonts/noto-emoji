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


EMOJI = NotoColorEmoji
font: $(EMOJI).ttf

CFLAGS = -std=c99 -Wall -Wextra `pkg-config --cflags --libs cairo`
LDFLAGS = `pkg-config --libs cairo`

waveflag: waveflag.c
	$(CC) $< -o $@ $(CFLAGS) $(LDFLAGS)

LIMITED_FLAGS = CN DE ES FR GB IT JP KR RU US
FLAGS = AD AE AF AG AI AL AM AO AR AS AT AU AW AX AZ \
	BA BB BD BE BF BG BH BI BJ BM BN BO BR BS BT BW BY BZ \
	CA CC CD CF CG CH CI CK CL CM CN CO CR CU CV CW CX CY CZ \
	DE DJ DK DM DO DZ \
	EC EE EG ER ES ET EU \
	FI FJ FM FO FR \
	GA GB GD GE GG GH GI GL GM GN GQ GR GT GU GW GY \
	HK HN HR HT HU \
	ID IE IL IM IN IO IQ IR IS IT \
	JE JM JO JP \
	KE KG KH KI KM KN KP KR KW KY KZ \
	LA LB LC LI LK LR LS LT LU LV LY \
	MA MC MD ME MG MH MK ML MM MN MO MP MR MS MT MU MV MW MX MY MZ \
	NA NE NF NG NI NL NO NP NR NU NZ \
	OM \
	PA PE PF PG PH PK PL PN PR PS PT PW PY \
	QA \
	RO RS RU RW \
	SA SB SC SD SE SG SI SK SL SM SN SO SR SS ST SV SX SY SZ \
	TC TD TG TH TJ TK TL TM TN TO TR TT TV TW TZ \
	UA UG US UY UZ \
	VA VC VE VG VI VN VU \
	WS \
	YE \
	ZA ZM ZW

FLAGS_SRC_DIR = ../third_party/region-flags/png
FLAGS_DIR = ./flags

FLAG_GLYPH_NAMES := $(shell ./flag_glyph_name.py $(FLAGS))

WAVED_FLAGS := $(foreach flag,$(FLAGS),$(FLAGS_DIR)/$(flag).png)
PNG128_FLAGS := $(foreach flag,$(FLAG_GLYPH_NAMES),$(addprefix ./png/128/emoji_$(flag),.png))
PNG64_FLAGS := $(foreach flag,$(FLAG_GLYPH_NAMES),$(addprefix ./png/64/emoji_,$(flag).png))

$(FLAGS_DIR)/%.png: $(FLAGS_SRC_DIR)/%.png ./waveflag
	mkdir -p $(FLAGS_DIR)
	./waveflag "$<" "$@"
	optipng -quiet -o7 "$@"

flag-symlinks: $(WAVED_FLAGS)
	for flag in $(FLAGS); do ln -fs ../../flags/$$flag.png ./png/128/emoji_`echo $$flag | ./flag_glyph_name.py`.png; done

$(PNG64_FLAGS): $(PNG128_FLAGS)

$(PNG128_FLAGS): flag-symlinks

EMOJI_PNG128 = ./png/128/emoji_u
EMOJI_PNG64 = ./png/64/emoji_u

EMOJI_BUILDER = ../third_party/color_emoji/emoji_builder.py
ADD_GLYPHS = ../third_party/color_emoji/add_glyphs.py
PUA_ADDER = ../nototools/map_pua_emoji.py

$(EMOJI_PNG64)%.png: $(EMOJI_PNG128)%.png
	convert -geometry 50% "$<" "$@"
	optipng -quiet -o7 "$@"

%.ttx: %.ttx.tmpl $(ADD_GLYPHS) $(UNI) flag-symlinks
	python $(ADD_GLYPHS) "$<" "$@" "$(EMOJI_PNG128)"

%.ttf: %.ttx
	@rm -f "$@"
	ttx "$<"

PNG64_IMAGES := $(patsubst $(EMOJI_PNG128)%,$(EMOJI_PNG64)%,$(wildcard $(EMOJI_PNG128)*.png)) $(PNG64_FLAGS)

$(EMOJI).ttf: $(EMOJI).tmpl.ttf $(EMOJI_BUILDER) $(PUA_ADDER) $(PNG64_IMAGES) $(EMOJI_PNG128)*.png flag-symlinks
	python $(EMOJI_BUILDER) -V $< "$@" $(EMOJI_PNG128) $(EMOJI_PNG64)
	python $(PUA_ADDER) "$@" "$@-with-pua"
	mv "$@-with-pua" "$@"

clean:
	rm -f $(EMOJI).ttf $(EMOJI).tmpl.ttf $(EMOJI).tmpl.ttx
	rm -f $(EMOJI_PNG64)*.png
	rm -f waveflag
	rm -rf $(FLAGS_DIR)
	rm -f `find -type l -name "*.png"`
