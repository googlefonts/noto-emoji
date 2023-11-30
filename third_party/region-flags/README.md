# 2023 Update

We no longer source flags from Wikipedia, preferring instead to acquire them directly
from the relevant government.

# Introduction

This package is a collection of flags for geographic region and sub-region codes.
The regions are based on the data from [BCP 47][0] and selected sub-regions (US
states, Canadian provinces and territories, and some sub-regions of Great Britain)
are based on [ISO 3166-2:US][1], [ISO 3166-2:CA][2], and [ISO-3166-2:GB][2].

Most people think of these regions from BCP 47 as country flags, but there are a
few codes / flags that do not correspond to countries. The flags are in SVG and
PNG format and named by their BCP 47 region code, which for countries is the same
as ISO 3166-2 country code. In case of sub-regions, ISO 3166-2 is used for naming
the files; e.g. `US-DE.png` is the flag of the State of Delaware.

The canonical way to get all BCP 47 region codes is to look for records in
`language-subtag-registry` (which is downloaded from [IANA Language Subtag
Registry][0]) with the following fields:

	Type: region
	Subtag: [A-Z]{2}
	AND NOT Description: Private use
	AND NOT Deprecated: .*

Regions not in that repository can be added to `language-subtag-private`.
One such region has been added.

Some regions do not have their own flag. In such cases, they are symlinked to
the best flag to represent them, which in most cases is the flag of their
regional or political parent. These are listed in file `ALIASES`.

The sub-regions currently covered are:

- US states and the District of Columbia
- Canadian provinces and territories
- Countries of England, Scotland, and Wales in Great Britain
- The province Northern Ireland in Great Britain

The flags are downloaded from Wikipedia. When Wikipedia flags were copyrighted,
we worked we Wikipedia editors to either relicense them, or drew / sourced and
uploaded new public-domain versions.  In particular, the license for these
flags were resolved for the initial import:

- Montenegro
- Nicaragua
- Sint Maarten
- Ascension Island
- Lesotho
- Kosovo

# Scripts

- The script `regions.py` lists all regions and some selected sub-regions with their metadata.
- The script `regions-wp.py` shows the Wikipedia URL for the flag page.
- The script `missing.sh` shows all such regions that we don't have flags for.
- The script `make-aliases.sh` makes symlinks for regions that use flag of another
region.
- The script `download-wp.py` downloads missing flags from Wikipedia and generating
optimized SVG and PNG versions.

You can use the [waveflag script from the Noto fonts project](../../waveflag.c)
to _wave_ PNG flags.

# Requirements

- Python 3
- [`dos2unix`](http://sourceforge.net/projects/dos2unix/)
- `rsvg-convert` part of [`librsvg`](https://wiki.gnome.org/Projects/LibRsvg)
- [`optipng`](http://optipng.sourceforge.net/)

# Updating

If new regions are needed, update `language-subtag-registry` from [IANA Language
Subtag Registry][0], or add new regions to `language-subtag-private` before.  Then
update `data/ALIASES` and `data/ALIASES-WP` as needed.

If a specific flag on Wikipedia flag is under Creative Commons, work with Wikipedia
editors to relicense it to public domain.  If the flag is not explicitly marked
`public_domain` but otherwise exempt from Copyright (typically, because of
national laws), make a note of it in file `COPYING`.

To download missing flags, run `download-wp.py`.

To update to latest flags from Wikipedia, delete the `html`, `svg`, and `png`
directories, then run `make-aliases.sh` followed by `download-wp.py`.


# License

See file `COPYING` for details.

[0]: http://www.iana.org/assignments/language-subtag-registry/language-subtag-registry
[1]: https://www.iso.org/obp/ui/#iso:code:3166:US
[2]: https://www.iso.org/obp/ui/#iso:code:3166:GB
[3]: https://www.iso.org/obp/ui/#iso:code:3166:CA
