![Noto](images/noto.png)
# Noto Emoji
Color and Black-and-White Noto emoji fonts, and tools for working with them.

## Building NotoColorEmoji

Building NotoColorEmoji currently requires a Python 2.x wide build.  To build
the emoji font you will require a few files from nototools.  Clone a copy from
https://github.com/googlei18n/nototools and either put it in your PYTHONPATH or
use 'python setup.py develop' ('install' currently won't fully install all the
data used by nototools).  You will also need fontTools, get it from
https://github.com/behdad/fonttools.git.

Then run make.  NotoColorEmoji is the default target.  It's suggested to use -j,
especially if you are using zopflipng for compression.  Intermediate products
(compressed image files, for example) will be put into a build subdirectory; the
font will be at the top level.

## Using NotoColorEmoji

NotoColorEmoji uses the CBDT/CBLC color font format, which is supported by Android
and Chrome/Chromium OS.  Windows supports it starting with Windows 10 Anniversary
Update in Chome and Edge.  On macOS, only Chrome supports it, while on Linux it will
support it with some fontconfig tweaking, see [issue #36](https://github.com/googlei18n/noto-emoji/issues/36). Currently we do not build other color font formats.

## Color emoji assets

The assets provided in the repo are all those used to build the NotoColorEmoji
font.  Note however that NotoColorEmoji often uses the same assets to represent
different character sequences-- notably, most gender-neutral characters or
sequences are represented using assets named after one of the gendered
sequences.  This means that some sequences appear to be missing.  Definitions of
the aliasing used appear in the emoji_aliases.txt file.

Also note that the images in the font might differ from the original assets.  In
particular the flag images in the font are PNG images to which transforms have
been applied to standardize the size and generate the wave and border shadow.  We
do not have SVG versions that reflect these transforms.

## B/W emoji font

The black-and-white emoji font is not under active development.  Its repertoire of
emoji is now several years old, and the design does not reflect the current color
emoji design.  Currently we have no plans to update this font.

## License

Emoji fonts (under the fonts subdirectory) are under the
[SIL Open Font License, version 1.1](fonts/LICENSE).<br/>
Tools and most image resources are under the [Apache license, version 2.0](./LICENSE).
Flag images under third_party/region-flags are in the public domain or
otherwise exempt from copyright ([more info](third_party/region-flags/LICENSE)).

## Contributing

Please read [CONTRIBUTING](CONTRIBUTING.md) if you are thinking of contributing to this project.

## News

* 2017-09-13: Emoji redesign released.
* 2015-12-09: Unicode 7 and 8 emoji image data (.png format) added.
* 2015-09-29: All Noto fonts now licensed under the SIL Open Font License.
