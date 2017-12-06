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
LDFLAGS = -lm `pkg-config --libs cairo`
PNGQUANTDIR := third_party/pngquant
PNGQUANT := $(PNGQUANTDIR)/pngquant
PNGQUANTFLAGS = --speed 1 --skip-if-larger --quality 85-95 --force
BODY_DIMENSIONS = 136x128
IMOPS := -size $(BODY_DIMENSIONS) canvas:none -compose copy -gravity center

# zopflipng is better (about 5-10%) but much slower.  it will be used if
# present.  pass ZOPFLIPNG= as an arg to make to use optipng instead.

ZOPFLIPNG = zopflipng
OPTIPNG = optipng

EMOJI_BUILDER = third_party/color_emoji/emoji_builder.py
ADD_GLYPHS = add_glyphs.py
ADD_GLYPHS_FLAGS = -a emoji_aliases.txt
PUA_ADDER = map_pua_emoji.py
VS_ADDER = add_vs_cmap.py # from nototools

EMOJI_SRC_DIR := png/128
FLAGS_SRC_DIR := third_party/region-flags/png

BUILD_DIR := build
EMOJI_DIR := $(BUILD_DIR)/emoji
FLAGS_DIR := $(BUILD_DIR)/flags
RESIZED_FLAGS_DIR := $(BUILD_DIR)/resized_flags
RENAMED_FLAGS_DIR := $(BUILD_DIR)/renamed_flags
QUANTIZED_DIR := $(BUILD_DIR)/quantized_pngs
COMPRESSED_DIR := $(BUILD_DIR)/compressed_pngs

# Unknown flag is PUA fe82b

LIMITED_FLAGS = CN DE ES FR GB IT JP KR RU US
SELECTED_FLAGS = AC AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ \
	BA BB BD BE BF BG BH BI BJ BM BN BO BR BS BT BW BY BZ \
	CA CC CD CF CG CH CI CK CL CM CN CO CR CU CV CW CX CY CZ \
	DE DJ DK DM DO DZ \
	EC EE EG ER ES ET EU \
	FI FJ FM FO FR \
	GA GB GD GE GG GH GI GL GM GN GQ GR GT GU GW GY \
	HK HN HR HT HU \
	IC ID IE IL IM IN IO IQ IR IS IT \
	JE JM JO JP \
	KE KG KH KI KM KN KP KR KW KY KZ \
	LA LB LC LI LK LR LS LT LU LV LY \
	MA MC MD ME MG MH MK ML MM MN MO MP MR MS MT MU MV MW MX MY MZ \
	NA NE NF NG NI NL NO NP NR NU NZ \
	OM \
	PA PE PF PG PH PK PL PN PR PS PT PW PY \
	QA \
	RO RS RU RW \
	SA SB SC SD SE SG SH SI SK SL SM SN SO SR SS ST SV SX SY SZ \
	TA TC TD TG TH TJ TK TL TM TN TO TR TT TV TW TZ \
	UA UG UN US UY UZ \
	VA VC VE VG VI VN VU \
	WS \
	YE \
	ZA ZM ZW \
        GB-ENG GB-SCT GB-WLS

ALL_FLAGS = $(basename $(notdir $(wildcard $(FLAGS_SRC_DIR)/*.png)))

FLAGS = $(SELECTED_FLAGS)

FLAG_NAMES = $(FLAGS:%=%.png)
FLAG_FILES = $(addprefix $(FLAGS_DIR)/, $(FLAG_NAMES))
RESIZED_FLAG_FILES = $(addprefix $(RESIZED_FLAGS_DIR)/, $(FLAG_NAMES))

FLAG_GLYPH_NAMES = $(shell ./flag_glyph_name.py $(FLAGS))
RENAMED_FLAG_NAMES = $(FLAG_GLYPH_NAMES:%=emoji_%.png)
RENAMED_FLAG_FILES = $(addprefix $(RENAMED_FLAGS_DIR)/, $(RENAMED_FLAG_NAMES))

EMOJI_NAMES = $(notdir $(wildcard $(EMOJI_SRC_DIR)/emoji_u*.png))
EMOJI_FILES= $(addprefix $(EMOJI_DIR)/,$(EMOJI_NAMES)))

ALL_NAMES = $(EMOJI_NAMES) $(RENAMED_FLAG_NAMES)

ALL_QUANTIZED_FILES = $(addprefix $(QUANTIZED_DIR)/, $(ALL_NAMES))
ALL_COMPRESSED_FILES = $(addprefix $(COMPRESSED_DIR)/, $(ALL_NAMES))

# tool checks
ifeq (,$(shell which $(ZOPFLIPNG)))
  ifeq (,$(wildcard $(ZOPFLIPNG)))
    MISSING_ZOPFLI = fail
  endif
endif

ifeq (,$(shell which $(OPTIPNG)))
  ifeq (,$(wildcard $(OPTIPNG)))
    MISSING_OPTIPNG = fail
  endif
endif

ifeq (, $(shell which $(VS_ADDER)))
  MISSING_ADDER = fail
endif


emoji: $(EMOJI_FILES)

flags: $(FLAG_FILES)

resized_flags: $(RESIZED_FLAG_FILES)

renamed_flags: $(RENAMED_FLAG_FILES)

quantized: $(ALL_QUANTIZED_FILES)

compressed: $(ALL_COMPRESSED_FILES)

check_compress_tool:
ifdef MISSING_ZOPFLI
  ifdef MISSING_OPTIPNG
	$(error "neither $(ZOPFLIPNG) nor $(OPTIPNG) is available")
  else
	@echo "using $(OPTIPNG)"
  endif
else
	@echo "using $(ZOPFLIPNG)"
endif

check_vs_adder:
ifdef MISSING_ADDER
	$(error "$(VS_ADDER) not in path, run setup.py in nototools")
endif


$(EMOJI_DIR) $(FLAGS_DIR) $(RESIZED_FLAGS_DIR) $(RENAMED_FLAGS_DIR) $(QUANTIZED_DIR) $(COMPRESSED_DIR):
	mkdir -p "$@"

$(PNGQUANT):
	$(MAKE) -C $(PNGQUANTDIR)

waveflag: waveflag.c
	$(CC) $< -o $@ $(CFLAGS) $(LDFLAGS)


# imagemagick's -extent operator munges the grayscale images in such a fashion
# that while it can display them correctly using libpng12, chrome and gimp using
# both libpng12 and libpng16 display the wrong gray levels.
#
# @convert "$<" -gravity center -background none -extent 136x128 "$@"
#
# We can get around the conversion to a gray colorspace in the version of
# imagemagick packaged with ubuntu trusty (6.7.7-10) by using -composite.

$(EMOJI_DIR)/%.png: $(EMOJI_SRC_DIR)/%.png | $(EMOJI_DIR)
	@convert $(IMOPS) "$<" -composite "PNG32:$@"

$(FLAGS_DIR)/%.png: $(FLAGS_SRC_DIR)/%.png ./waveflag $(PNGQUANT) | $(FLAGS_DIR)
	@./waveflag $(FLAGS_DIR)/ "$<"

$(RESIZED_FLAGS_DIR)/%.png: $(FLAGS_DIR)/%.png | $(RESIZED_FLAGS_DIR)
	@convert $(IMOPS) "$<" -composite "PNG32:$@"

flag-symlinks: $(RESIZED_FLAG_FILES) | $(RENAMED_FLAGS_DIR)
	@$(subst ^, ,                                  \
	  $(join                                       \
	    $(FLAGS:%=ln^-fs^../resized_flags/%.png^), \
	    $(RENAMED_FLAG_FILES:%=%; )                \
	   )                                           \
	 )

$(RENAMED_FLAG_FILES): | flag-symlinks

$(QUANTIZED_DIR)/%.png: $(RENAMED_FLAGS_DIR)/%.png $(PNGQUANT) | $(QUANTIZED_DIR)
	@($(PNGQUANT) $(PNGQUANTFLAGS) -o "$@" "$<"; case "$$?" in "98"|"99") echo "reuse $<"; cp $< $@;; *) exit "$$?";; esac)

$(QUANTIZED_DIR)/%.png: $(EMOJI_DIR)/%.png $(PNGQUANT) | $(QUANTIZED_DIR)
	@($(PNGQUANT) $(PNGQUANTFLAGS) -o "$@" "$<"; case "$$?" in "98"|"99") echo "reuse $<";cp $< $@;; *) exit "$$?";; esac)

$(COMPRESSED_DIR)/%.png: $(QUANTIZED_DIR)/%.png | check_compress_tool $(COMPRESSED_DIR)
ifdef MISSING_ZOPFLI
	@$(OPTIPNG) -quiet -o7 -clobber -force -out "$@" "$<"
else
	@$(ZOPFLIPNG) -y "$<" "$@" 1> /dev/null 2>&1
endif


# Make 3.81 can endless loop here if the target is missing but no
# prerequisite is updated and make has been invoked with -j, e.g.:
# File `font' does not exist.
#      File `NotoColorEmoji.tmpl.ttx' does not exist.
# File `font' does not exist.
#      File `NotoColorEmoji.tmpl.ttx' does not exist.
# ...
# Run make without -j if this happens.

%.ttx: %.ttx.tmpl $(ADD_GLYPHS) $(ALL_COMPRESSED_FILES)
	@python $(ADD_GLYPHS) -f "$<" -o "$@" -d "$(COMPRESSED_DIR)" $(ADD_GLYPHS_FLAGS)

%.ttf: %.ttx
	@rm -f "$@"
	ttx "$<"

$(EMOJI).ttf: $(EMOJI).tmpl.ttf $(EMOJI_BUILDER) $(PUA_ADDER) \
	$(ALL_COMPRESSED_FILES) | check_vs_adder
	@python $(EMOJI_BUILDER) -V $< "$@" "$(COMPRESSED_DIR)/emoji_u"
	@python $(PUA_ADDER) "$@" "$@-with-pua"
	@$(VS_ADDER) -vs 2640 2642 2695 --dstdir '.' -o "$@-with-pua-varsel" "$@-with-pua"
	@mv "$@-with-pua-varsel" "$@"
	@rm "$@-with-pua"

clean:
	rm -f $(EMOJI).ttf $(EMOJI).tmpl.ttf $(EMOJI).tmpl.ttx
	rm -f waveflag
	rm -rf $(BUILD_DIR)

.SECONDARY: $(EMOJI_FILES) $(FLAG_FILES) $(RESIZED_FLAG_FILES) $(RENAMED_FLAG_FILES) \
  $(ALL_QUANTIZED_FILES) $(ALL_COMPRESSED_FILES)

.PHONY:	clean flags emoji renamed_flags quantized compressed check_compress_tool

