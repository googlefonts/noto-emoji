# delete dst, then:
# copy the placeholders to dst
# then copy the noto images to dst
# then copy the draft images to dst, skipping names with parens and
# after fixing the case of the names

import glob
import os
from os import path
import re
import shutil

DST = '/tmp/placeholder_emoji_plus'

SRC_PLACEHOLDER = '/usr/local/google/users/dougfelt/emoji_images/placeholder'
SRC_NOTO = '/usr/local/google/users/dougfelt/newnoto/noto-emoji/png/128'
SRC_DRAFT = '/usr/local/google/users/dougfelt/emoji_images/png_thurs'

# First, scan the draft images and select which ones to use.  This does
# two things:
# - The download package returns all the images, including previous versions.
#   Ensure we use the one with the highest version.
# - The names often mix case.  Make sure we have all lower case names.
#
# If something seems amiss, we fail.

UPDATED_NAMES = {}
FIXED_NAMES = {}
VAR_PAT = re.compile(r'(.*?)\((\d+)\)\.png')
for fname in glob.glob(path.join(SRC_DRAFT, '*.png')):
  name = path.basename(fname)
  if 'alt' in name:
    print 'skip %s' % name
    continue

  m = VAR_PAT.match(name)
  if m:
    name = '%s.png' % m.group(1).lower()
    version = int(m.group(2))
    if version > UPDATED_NAMES.get(name, (0, None))[0]:
      print 'update %s to version %d' % (name, version)
      UPDATED_NAMES[name] = (version, fname)
  else:
    name = name.lower()
    FIXED_NAMES[name] = fname

for name in UPDATED_NAMES:
  if name not in FIXED_NAMES:
    raise Exception('updated name %s not in names' % name)
  fname = UPDATED_NAMES[name][1]
  print 'using updated image %s for %s' % (fname, name)
  FIXED_NAMES[name] = fname

EXCLUDE_PAT = re.compile(r'emoji_u1f3f[bcdef].png')
remove = [name for name in FIXED_NAMES if EXCLUDE_PAT.match(name)]
for name in remove:
  print 'removing %s' % name
  del FIXED_NAMES[name]


# Now, recreate the destination directory and copy the data into it.

if path.isdir(DST):
  shutil.rmtree(DST)
os.makedirs(DST)

def flag_emoji_name(flag_ascii):
  return 'emoji_u%s.png' % '_'.join(
      '%04x' % (ord(cp) - ord('A') + 0x1f1e6) for cp in flag_ascii)

SKIP_FLAGS = [flag_emoji_name(name) for name in [
    'AC', 'AQ', 'BL', 'BQ', 'BV', 'CP', 'DG', 'EA', 'EH', 'FK',
    'GF', 'GP', 'GS', 'HM', 'IC', 'MF', 'MQ', 'NC', 'PM', 'RE',
    'SH', 'SJ', 'TA', 'TF', 'UM', 'WF', 'XK', 'YT',
    ]]

def emoji_name(val):
  return 'emoji_u%04x.png' % val

SKIP_SWATCHES = [emoji_name(val) for val in range(0x1f3fb, 0x1f3ff + 1)]

# these are placeholders for emoji that have a single codepoint yet
# also have a decomposition.
# we want to use the image for the single codepoint.
SKIP_SINGLE_CP_EMOJI = [
  'emoji_u1f468_200d_1f469_200d_1f466.png',
  'emoji_u1f469_200d_2764_fe0f_200d_1f468.png',
  'emoji_u1f469_200d_2764_fe0f_200d_1f48b_200d_1f468.png',
]

SKIP_PLACEHOLDERS = frozenset(SKIP_FLAGS + SKIP_SWATCHES + SKIP_SINGLE_CP_EMOJI)

for fname in sorted(glob.glob(path.join(SRC_PLACEHOLDER, '*.png'))):
  basename = path.basename(fname)
  if basename in SKIP_PLACEHOLDERS:
    print 'skip placeholder %s' % basename
    continue
  shutil.copy(fname, DST)

for fname in glob.glob(path.join(SRC_NOTO, '*.png')):
  shutil.copy(fname, DST)

for name, fname in FIXED_NAMES.iteritems():
  shutil.copy(fname, path.join(DST, name))
