![Noto](images/noto.png)
# Noto Emoji
Color and Black-and-White Noto emoji fonts, and tools for working with them.

The color version must be built from source.

## Building NotoColorEmoji

Building NotoColorEmoji requires a few files from nototools.  Clone a copy from
https://github.com/googlei18n/nototools and either put it in your PYTHONPATH or
use 'python setup.py develop' ('install' currently won't fully install all the
data used by nototools).

Then run make.  NotoColorEmoji is the default target.  It's suggested to use -j,
especially if you are using zopflipng for compression.  Intermediate products
(compressed image files, for example) will be put into a build subdirectory; the
font will be at the top level.

## License

Emoji fonts (under the fonts subdirectory) are under the
[SIL Open Font License, version 1.1](fonts/LICENSE).<br/>
Tools are under the [Apache license, version 2.0](./LICENSE).

## Contributing

Please read [CONTRIBUTING](CONTRIBUTING.md) if you are thinking of contributing to this project.

## News

* 2015-12-09: Unicode 7 and 8 emoji image data (.png format) added.
* 2015-09-29: All Noto fonts now licensed under the SIL Open Font License.
