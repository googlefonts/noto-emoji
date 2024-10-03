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

## Rebuild the fonts

```bash
# Build CBDT, COLR, flags-only, and emojicompat fonts
$ ./full_rebuild.sh
```
