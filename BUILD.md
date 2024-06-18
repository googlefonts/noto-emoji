# Build instructions

Typically build the CBDT then the COLRv1 as COLRv1 copies some information from CBDT.

## Is this a Unicode rev?

* Update https://github.com/notofonts/nototools, publish the new version
   * Must be done by a Googler. See internal instructions.
* Update emojicompat
   * https://github.com/googlefonts/emojicompat?tab=readme-ov-file#support-new-unicode-sequences
* Update artwork
   * Must be done by a Googler. Work with the emoji design team using internal instructions.

## Update version

Edit `NotoColorEmoji.tmpl.ttx.tmpl`
*   In `<head>` find `fontRevision`.
    *   It should be of the form 2.xxx
    *   Increment xxx by 1
*   In `<name>` find `<namerecord nameID="5" platformID="3" platEncID="1"
    langID="0x409">`
    *   It should look like `Version
        2.017;GOOG;noto-emoji:20180810:f1da3bc656f9`
    *   Update Version to match `<head>` (`Version 2.017` in the example)
    *   Update the date (`20180810` in the example)
    *   Update the commit

## Update new flags

* Add new flags to list in Makefile ([example](https://github.com/googlefonts/noto-emoji-next/commit/21bdd6107fac60979737ac95c2655cb02824d144))
* Update `third_party/region-flags`. For example, for CQ (Sark) update:
   * `third_party/region-flags/png/CQ.png`
      * This file can be highres, it will be resized by the CBDT build process
      * This file should have the proportions of the flag
   * `third_party/region-flags/svg/CQ.svg`
      * This file is *not* required to have the `0 0 128 128` viewbox files in `/svg` have to have
   * `third_party/region-flags/waved-svg/emoji_u1f1e8_1f1f6.svg`
      * This file is produced using https://github.com/rsheeter/warp
      * New flags are added to `wave_list.txt`
         * To wave only the new flag delete other entries locally

## CBDT

```bash
rm -rf venv  # in case you have an old borked venv!
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python size_check.py
rm -rf build/ && time make -j 48
# Should take 2-3 minutes to create noto-emoji/NotoColorEmoji.ttf

mv *.ttf fonts/

# make noflags CBDT font
rm fonts/NotoColorEmoji-noflags.ttf
python drop_flags.py fonts/NotoColorEmoji.ttf
```

## COLRv1

```bash
# If you are updating to a new Unicode rev, update configs
python colrv1_generate_configs.py
git diff colrv1/*.toml

# Compile the fonts
(cd colrv1 && rm -rf build/ && time nanoemoji *.toml)
cp colrv1/build/NotoColorEmoji.ttf fonts/Noto-COLRv1.ttf
cp colrv1/build/NotoColorEmoji-noflags.ttf fonts/Noto-COLRv1-noflags.ttf

# Post-process them
python colrv1_postproc.py
```

## Emojicompat

```
# Add support for new sequences per https://github.com/googlefonts/emojicompat#support-new-unicode-sequences
# Install https://github.com/googlefonts/emojicompat in a venv
# Create emojicompat versions of the fonts you made
# Starting from the root of noto-emoji-next:

$ pushd fonts
$ cp NotoColorEmoji.ttf NotoColorEmoji-emojicompat.ttf
$ cp Noto-COLRv1.ttf Noto-COLRv1-emojicompat.ttf
$ emojicompat --op setup --font NotoColorEmoji-emojicompat.ttf
$ emojicompat --op setup --font Noto-COLRv1-emojicompat.ttf
$ emojicompat --op check --font NotoColorEmoji-emojicompat.ttf
$ emojicompat --op check --font Noto-COLRv1-emojicompat.ttf

# The emojicompat --op check step should print something akin to:
3835 items_by_codepoints
0 PUA missing
0 PUA point at wrong glyph
3835 PUA correct
0 Emji entries did NOT match a glyph
```

## Flags only

```bash
$ hb-subset --unicodes-file=flags-only-unicodes.txt \
	--output-file=fonts/NotoColorEmoji-flagsonly.ttf \
	fonts/NotoColorEmoji.ttf
$ python update_flag_name.py
```