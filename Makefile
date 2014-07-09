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

FONT = NotoColorEmoji
PNGS_PREFIX1 = ./png/128/emoji_u
PNGS_PREFIX2 = ./png/64/emoji_u

EMOJI_BUILDER = ../third_party/color_emoji/emoji_builder.py
ADD_GLYPHS= ../third_party/color_emoji/add_glyphs.py

%.ttx: %.ttx.tmpl $(ADD_GLYPHS) $(UNI)
	python $(ADD_GLYPHS) "$<" "$@" "$(PNGS_PREFIX1)"

%.ttf: %.ttx
	@rm -f "$@"
	ttx "$<"

$(FONT).ttf: $(FONT).tmpl.ttf $(EMOJI_BUILDER) $(PNGS_PREFIX1)*.png $(PNGS_PREFIX2)*.png
	python $(EMOJI_BUILDER) -V $< "$@" $(PNGS_PREFIX1) $(PNGS_PREFIX2)

clean:
	rm -f $(FONT).ttf $(FONT).tmpl.ttf $(FONT).tmpl.ttx
