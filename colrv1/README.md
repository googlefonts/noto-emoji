# COLRv1 Build

We assume the bitmap version with equivalent coverage exists and
contains emojicompat metadata.

## Build Steps

1. Check the list of sources in the config files is in sync with the current sources

   ```shell
   # running from the noto-emoji repository root directory
   python colrv1_generate_configs.py
   git diff colrv1/*.toml
   ```

   If configs are in sync, the `colrv1/*.toml` files should contain no diffs.

1. Compile the COLRv1 fonts

   ```shell
   time nanoemoji *.toml
   cp build/NotoColorEmoji.ttf ../fonts/Noto-COLRv1.ttf
   cp build/NotoColorEmoji-noflags.ttf ../fonts/Noto-COLRv1-noflags.ttf
   ```

1. Post-process COLRv1 fonts
   * Adds some additional sequences, fixes up `name`, etc
   * At time of writing only the noflags version is for Android

   ```shell
   # Assumed to be in a python3 environment with requirements.txt fulfilled
   python colrv1_postproc.py
   ```

1. Add emojicompat metadata to the Android font and pass to the Android team
   * TODO write detailed instructions