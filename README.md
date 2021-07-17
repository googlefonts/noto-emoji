#### DISCLAIMER:
I am **neither** affiliated nor in _any_ relationship to the original creators or to Emojipedia or anything or anyone else.

![Noto](images/noto.png)
# Noto Emoji with Blobs enabled

This repository is intended to continue the development of the Blob emojis which have been abandoned by the original creators in 2017.

My goal is to upgrade the Blob emojis with a fresh style which is consistent to other emoji vendors.

Another thing is that this emoji set includes some emojis and ZWJ-sequences which are not part of the current emoji standard (although some or most of them are about to be included in the upcoming Unicode-standard), which means it might be one of the biggest emoji sets currently available!

Please note that I did not create most of the emojis. You can find an overview of the changes I made in the file CHANGES.txt

Most information on this fork will be included in the [Wiki](https://github.com/C1710/blobmoji/wiki). There you'll find more detailed build instructions and other helpful information on how to use this font and much more.  
If you want to use this font - there's a [Wiki page](https://github.com/C1710/blobmoji/wiki/Installation-Usage) :D

(_[Emojipedia®](https://emojipedia.org) is a registered trademark of Emojipedia Pty Ltd_)

But now to the original content of this Readme:

# Noto Emoji

Color and Black-and-White Noto emoji fonts, and tools for working with them.

## ~~Building NotoColorEmoji~~

~~Building NotoColorEmoji currently requires a Python 2.x wide build.  To build
the emoji font you will require a few files from nototools.  Clone a copy from
https://github.com/googlei18n/nototools and either put it in your PYTHONPATH or
use 'python setup.py develop' ('install' currently won't fully install all the
data used by nototools).  You will also need fontTools, get it from
https://github.com/behdad/fonttools.git.~~

~~Then run `make`.  NotoColorEmoji is the default target.  It's suggested to use `-j`,
especially if you are using zopflipng for compression.  Intermediate products
(compressed image files, for example) will be put into a build subdirectory; the
font will be at the top level.~~

## Building Blobmoji 13+

_Building is now done using [emoji_builder](https://github.com/C1710/emoji_builder/) (name WIP). Once you have it running, you can build it using the following command (you'll need to replace `emoji_builder` by the executable you use, e.g. `emoji_builder.exe` and maybe including the path. I recommend copying it into the `blobmoji`-directory):_
```
emoji_builder --flags ./third_party/region-flags/svg blobmoji -w -a ./emoji_aliases.txt --ttx-tmpl ./NotoColorEmoji.tmpl.ttx.tmpl --palette ./Blobmoji.gpl --default_font "Comic Neue"
```
- `--flags`: Use the directory conaining the flags
- `-w` add a wave-effect to the flags
- `-a` use an alias file
- `--ttx-tmpl` Use the template for the font metadata
- `--palette` normalize the colors to a specific color palette in the GIMP format (which is a derivation of the color palette present in the [2014 _Material Design_](https://material.io/archive/guidelines/style/color.html#color-color-palette))
- `--default_font` Because the graphics program I currently use (Affinity Designer) outputs font specifications in a format that `resvg`/`emoji_builder` has issues with, the font is explicitly specified here (note that if the font is correctly recognized, this one is not used. So as of now it is _not_ used to use a font for _all_ emojis)

## ~~Docker build~~

~~Alternatively, you can also build the font within Docker through the provided Dockerfile.
Just run `docker build . -t blobmoji && docker run --rm -it -v "$PWD/output:/output" blobmoji`. The resulting font will reside in the 'output' folder in your current working directory.~~

The Docker build method isn't available for `emoji_builder` yet

## Using NotoColorEmoji

NotoColorEmoji uses the CBDT/CBLC color font format, which is supported by Android
and Chrome/Chromium OS, but not macOS.  Windows supports it starting with Windows 10
Anniversary Update.   No Browser on macOS supports it, but Edge (on latest Windows)
does.  Chrome on Linux will support it with some fontconfig tweaking, see
[issue #36](https://github.com/googlei18n/noto-emoji/issues/36). Currently we do
not build other color font formats.

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

 > Emoji fonts (under the fonts subdirectory) are under the
[SIL Open Font License, version 1.1](fonts/LICENSE).<br/>
Tools and most image resources are under the [Apache license, version 2.0](./LICENSE).
Flag images under third_party/region-flags are in the public domain or
otherwise exempt from copyright ([more info](third_party/region-flags/LICENSE)).

_First of all, this licensing is used for this project too to avoid any confusion. This might be extended in the future for all files entirely made by myself._

## Contributing

 > Please read [CONTRIBUTING](CONTRIBUTING.md) if you are thinking of contributing to this project.

_Note: On this fork you can simply send pull requests or issues. I'll try to respond as soon as possible._

_Please try to use the discussion feature for artistic topics, like the style of the emojis. Issues are better suited for real issues, like not being able to use the font or really **missing** characters, etc._

## News
* _2018-02-03: Blobmoji Fork created_
* 2017-09-13: Emoji redesign released.
* 2015-12-09: Unicode 7 and 8 emoji image data (.png format) added.
* 2015-09-29: All Noto fonts now licensed under the SIL Open Font License.


_Microsoft, Windows are trademarks of the Microsoft group of companies._