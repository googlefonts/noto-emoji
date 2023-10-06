# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Generate config files for Noto-COLRv1

from nanoemoji.util import rel
from pathlib import Path


_NOTO_FAMILY_NAME = "Noto Color Emoji"
_NOTO_SVG_DIR = Path("svg")
_REGIONAL_INDICATORS = {
    Path(_NOTO_SVG_DIR / f"emoji_u{i:x}.svg") for i in range(0x1F1E6, 0x1F1FF + 1)
}
_NOTO_WAVED_FLAG_SVG_DIR = Path("third_party/region-flags/waved-svg")
_NOTO_SUBDIVISION_FLAGS = (
    _NOTO_WAVED_FLAG_SVG_DIR / "emoji_u1f3f4_e0067_e0062_e0065_e006e_e0067_e007f.svg",
    _NOTO_WAVED_FLAG_SVG_DIR / "emoji_u1f3f4_e0067_e0062_e0073_e0063_e0074_e007f.svg",
    _NOTO_WAVED_FLAG_SVG_DIR / "emoji_u1f3f4_e0067_e0062_e0077_e006c_e0073_e007f.svg",
)
_CONFIG_DIR = Path("colrv1")


def _write_config(config_name, output_file, svg_files):
    svg_files = [rel(_CONFIG_DIR, Path(f)) for f in svg_files]
    config_file = f"{config_name}.toml"
    for svg_file in svg_files:
        assert _CONFIG_DIR.joinpath(
            svg_file
        ).is_file(), f"{svg_file} not found relative to {_CONFIG_DIR}"
    svg_list = ",\n    ".join(f'"{f}"' for f in sorted(svg_files)).rstrip()
    with open(_CONFIG_DIR / config_file, "w") as f:
        f.write(
            f"""
family = "{_NOTO_FAMILY_NAME}"
output_file = "{output_file}"
color_format = "glyf_colr_1"
clipbox_quantization = 32

[axis.wght]
name = "Weight"
default = 400

[master.regular]
style_name = "Regular"
srcs = [
    {svg_list},
]

[master.regular.position]
wght = 400
"""
        )


def _write_all_noto_configs():
    # includes all of noto-emoji svgs plus all the waved region flags
    regular = tuple(_NOTO_SVG_DIR.glob("*.svg"))
    flags = tuple(_NOTO_WAVED_FLAG_SVG_DIR.glob("*.svg"))

    dups = {p.name for p in regular} & {p.name for p in flags}
    if dups:
        raise ValueError(f"Flags *and* regular have {dups}")

    svgs = regular + flags
    _write_config("all", "NotoColorEmoji.ttf", svgs)


def _write_noto_noflag_configs():
    # Does not contain regional indicators and the region flags that are
    # composed with them. It still includes the England, Scotland and Wales
    # 'subdivision' flags, as those are not composed with Unicode regional
    # indicators, but use sequences of Unicode Tag letters prefixed with
    # the Black Flag and ending with a Cancel Tag.
    svgs = (
        tuple(p for p in _NOTO_SVG_DIR.glob("*.svg") if p not in _REGIONAL_INDICATORS)
        + _NOTO_SUBDIVISION_FLAGS
    )
    _write_config("noflags", "NotoColorEmoji-noflags.ttf", svgs)


def main():
    _write_all_noto_configs()
    _write_noto_noflag_configs()


if __name__ == "__main__":
    main()
