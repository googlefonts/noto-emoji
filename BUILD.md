# Build instructions

Typically build the CBDT then the COLRv1 as COLRv1 copies some information from CBDT.

## CBDT

```bash
rm -rf venv  # in case you have an old borked venv!
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python size_check.py
rm -rf build/ && time make -j 48
# Should take 2-3 minutes to create noto-emoji/NotoColorEmoji.ttf

mv *.ttf fonts/
```

## COLRv1

```bash
# If you are updating to a new Unicode rev, update configs
python colrv1_generate_configs.py
git diff colrv1/*.toml

# Compile the fonts
(cd colrv1 && rm -rf build/ && time nanoemoji *.toml)
cp colrv1/build/NotoColorEmoji.ttf fonts/Noto-COLRv1.ttf
cp colrv1/build/NotoColorEmoji-noflags.ttf fonts/Noto-COLRv1-noflags.ttf

# Post-process them
python colrv1_postproc.py
```

## Emojicompat

```
# Add support for new sequences per https://github.com/googlefonts/emojicompat#support-new-unicode-sequences
# Install https://github.com/googlefonts/emojicompat in a venv
# Create emojicompat versions of the fonts you made
# Starting from the root of noto-emoji-next:

$ pushd fonts
$ cp NotoColorEmoji.ttf NotoColorEmoji-emojicompat.ttf
$ cp Noto-COLRv1.ttf Noto-COLRv1-emojicompat.ttf
$ emojicompat --op setup --font NotoColorEmoji-emojicompat.ttf
$ emojicompat --op setup --font Noto-COLRv1-emojicompat.ttf
$ emojicompat --op check --font NotoColorEmoji-emojicompat.ttf
$ emojicompat --op check --font Noto-COLRv1-emojicompat.ttf

# The emojicompat --op check step should print something akin to:
3835 items_by_codepoints
0 PUA missing
0 PUA point at wrong glyph
3835 PUA correct
0 Emji entries did NOT match a glyph
