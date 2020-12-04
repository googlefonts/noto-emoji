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

"""One-off tool to rename flags to the emoji_u format.

Delete late, use the proper emoji_u naming ongoing.
"""


import os
from pathlib import Path


# Some flags have especially fun RGIs
_FUN_RGIS = {
    "GB-ENG": (0x1f3f4, 0xe0067, 0xe0062, 0xe0065, 0xe006e, 0xe0067, 0xe007f),
    "GB-SCT": (0x1f3f4, 0xe0067, 0xe0062, 0xe0073, 0xe0063, 0xe0074, 0xe007f),
    "GB-WLS": (0x1f3f4, 0xe0067, 0xe0062, 0xe0077, 0xe006c, 0xe0073, 0xe007f),
}


def _is_legacy_flag(p):
    return p.stem in _FUN_RGIS or (
        len(p.stem) == 2 and all('A' <= c <= 'Z' for c in p.stem)
    )


def _flag_rename(f):
  """Converts a file name from two-letter upper-case ASCII to our expected
  'emoji_uXXXXX_XXXXX form, mapping each character to the corresponding
  regional indicator symbol."""

  cp_strs = []
  name = f.stem
  ext = f.suffix
  if name not in _FUN_RGIS:
    if len(name) != 2:
      raise ValueError('illegal flag name "%s"' % f)
    for cp in name:
      if not ('A' <= cp <= 'Z'):
        raise ValueError('illegal flag name "%s"' % f)
      ncp = 0x1f1e6 - 0x41 + ord(cp)
      cp_strs.append("%04x" % ncp)
  else:
    cp_strs = ["%04x" % cp for cp in _FUN_RGIS[name]]
  return f.parent / ('emoji_u%s%s' % ('_'.join(cp_strs), ext))


def main():
  for file in Path("third_party/waved-flags").glob("**/*.*"):
    if _is_legacy_flag(file):
        modern_name = _flag_rename(file)
        print(file, "=>", modern_name)
        file.rename(modern_name)


if __name__ == '__main__':
  main()
