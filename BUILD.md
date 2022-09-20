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
(cd colrv1 && python colrv1_generate_configs.py)
git diff colrv1/*.toml

# Compile the fonts
(cd colrv1 && rm -rf build/ && time nanoemoji *.toml)
cp colrv1/build/NotoColorEmoji.ttf fonts/Noto-COLRv1.ttf
cp colrv1/build/NotoColorEmoji-noflags.ttf fonts/Noto-COLRv1-noflags.ttf

# Post-process them
python colrv1_postproc.py
```

## Emojicompat

TODO detailed instructions