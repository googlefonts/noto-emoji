# Introduction

This package is a collection of flags for BCP 47 region codes.  Most people
think of these as country flags, but there are a few codes / flags that do
not correspond to countries.  The flags are in SVG and PNG format and named
by their BCP 47 region code, which for countries is the same as ISO 3166-2
country code.

The canonical way to get all region codes is to look for records in
language-subtag-registry (which is downloaded from [0]) with the following
fields:

	Type: region
	Subtag: [A-Z]{2}
	AND NOT Description: Private use
	AND NOT Deprecated: .*

Regions not in that repository can be added to language-subtag-private.
One such region has been added.

Some regions do not have their own flag.  In such cases, they are symlinked to
the best flag to represent them, which in most cases is the flag of their
regional or political parent.  These are listed in file ALIASES.

The flags are downloaded from Wikipedia.  When Wikipedia flags were
copyrighted, we worked we Wikipedia editors to either relicense them, or drew /
sourced and uploaded new public-domain versions.  In particular, the license
for these flags were resolved for the initial import:

  Montenegro
  Nicaragua
  Sint Maarten
  Ascension Island
  Lesotho
  Kosovo


# Scripts

The script regions.py lists all regions with their metadata.

The script regions-wp.py shows the Wikipedia URL for the flag page.

The script missing.sh shows all such regions that we don't have flags for.

The script make-aliases.sh makes symlinks for regions that use flag of
another region.

The script download-wp.py downloads missing flags from Wikipedia and
generating optimized SVG and PNG versions.


# Updating

If new regions are needed, update language-subtag-registry [0], or add new
regions to language-subtag-private before.  Then update ALIASES and ALIASES-WP
as needed.

If Wikipedia's flag is under Creative Commons, work with Wikipedia editors to
relicense it to public domain.  If the flag is not explicitly marked
public_domain but otherwise exempt from copyright (typically, because of
national laws), make a note of it in file COPYING.

To download missing flags, run download-wp.py.

To update to latest flags from Wikipedia, delete the html, svg, and png
directories, then run make-aliases.sh followed by download-wp.py.


# License

See file COPYING for details.


# References

[0] http://www.iana.org/assignments/language-subtag-registry/language-subtag-registry
