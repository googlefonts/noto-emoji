#!/usr/bin/env python3
# Copyright 2020 Google, Inc. All Rights Reserved.
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

"""Exploratory over-simplified tool for application of the specific form
of style that seems to exist in the flag svgs.
"""


from lxml import etree
import os
from pathlib import Path
import re


_SVGNS = {"svg": 'http://www.w3.org/2000/svg'}
# specific to the narrow usage of style in flag svgs
_STYLE_RE = re.compile(r"[.](\w+)\{([^}]+)\}$")


def main():
  for file in Path("third_party/waved-flags/svg").glob("emoji_u*.svg"):
    print(file)
    tree = etree.parse(str(file))
    root = tree.getroot()
    style_els = root.xpath("//svg:style", namespaces=_SVGNS)
    if not style_els:
      print("skip", file)
      continue
    if len(style_els) > 1:
      print("ERROR multiple style elements", file)
      continue

    style = style_els[0]
    style.getparent().remove(style)

    for style_line in style.text.split("\n"):
      style_line = style_line.strip()
      if not style_line:
        continue
      match = _STYLE_RE.match(style_line)
      assert match, f"Unsupported line '{style_line}' in {file}"
      class_name = match.group(1).strip()
      styles = {s.strip() for s in match.group(2).split(";") if s.strip()}

      styled_els = root.xpath(f"//svg:*[@class='{class_name}']", namespaces=_SVGNS)
      for style in sorted(styles):
        name, value = (v.strip() for v in style.split(":"))
        for el in styled_els:
          el.attrib[name] = value
      for el in styled_els:
        assert el.attrib["class"] == class_name
        del el.attrib["class"]

      etree.ElementTree(root).write(str(file), pretty_print=True)


if __name__ == '__main__':
  main()
