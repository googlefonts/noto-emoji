#!/usr/bin/env bash

set -e
set -v

# We have to have hb-subset on PATH
which hb-subset

# Build the CBDT font

rm -rf venv  # in case you have an old borked venv!
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

rm -rf emojicompat
git clone git@github.com:googlefonts/emojicompat.git
pip install emojicompat/

# Validation
python size_check.py
rm -rf build/ && time make -j 48
# Should take 2-3 minutes to create noto-emoji/NotoColorEmoji.ttf

mv *.ttf fonts/

# make noflags CBDT font
rm fonts/NotoColorEmoji-noflags.ttf
python drop_flags.py fonts/NotoColorEmoji.ttf

# Build the COLRv1 font (slow)

python colrv1_generate_configs.py
git diff colrv1/*.toml

# Compile the fonts
# Should take ~20 minutes
(cd colrv1 && rm -rf build/ && time nanoemoji *.toml)
cp colrv1/build/NotoColorEmoji.ttf fonts/Noto-COLRv1.ttf
cp colrv1/build/NotoColorEmoji-noflags.ttf fonts/Noto-COLRv1-noflags.ttf

# Post-process them
python colrv1_postproc.py

# Produce emojicompat variants
# Add support for new sequences per https://github.com/googlefonts/emojicompat#support-new-unicode-sequences

pushd fonts
cp NotoColorEmoji.ttf NotoColorEmoji-emojicompat.ttf
cp Noto-COLRv1.ttf Noto-COLRv1-emojicompat.ttf
emojicompat --op setup --font NotoColorEmoji-emojicompat.ttf
emojicompat --op setup --font Noto-COLRv1-emojicompat.ttf
emojicompat --op check --font NotoColorEmoji-emojicompat.ttf
emojicompat --op check --font Noto-COLRv1-emojicompat.ttf
popd

hb-subset --unicodes-file=flags-only-unicodes.txt \
   --output-file=fonts/NotoColorEmoji-flagsonly.ttf \
   fonts/NotoColorEmoji.ttf
python update_flag_name.py