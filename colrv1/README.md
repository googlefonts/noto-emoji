# COLRv1 Build

Assumptions:

* bitmap font already exists.
* a font that contains complete emojicompat metadata exists

## Build Steps

1. Compile the COLRv1 fonts

   ```shell
   time nanoemoji *.toml
   ```

1. Post-process COLRv1 font for Android
   * At time of writing only the noflags version is for Android