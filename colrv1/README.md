# COLRv1 Build

We assume the bitmap version with equivalent coverage exists and
contains emojicompat metadata.

## Build Steps

1. Compile the COLRv1 fonts

   ```shell
   time nanoemoji *.toml
   ```

1. Post-process COLRv1 font for Android
   * At time of writing only the noflags version is for Android

   ```shell
   # Assumed to be in a python3 environment with requirements.txt fulfilled
   python colrv1_postproc.py colrv1/build/NotoColorEmoji-noflags.ttf \
   	PATH_TO/NotoColorEmojiCompat.ttf
   ```