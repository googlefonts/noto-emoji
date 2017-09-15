from __future__ import print_function
import os
from os import path
import subprocess

OUTPUT_DIR = '/tmp/placeholder_emoji'

def generate_image(name, text):
  print(name, text.replace('\n', '_'))
  subprocess.check_call(
      ['convert', '-size', '100x100', 'label:%s' % text,
       '%s/%s' % (OUTPUT_DIR, name)])

def is_color_patch(cp):
  return cp >= 0x1f3fb and cp <= 0x1f3ff

def has_color_patch(values):
  for v in values:
    if is_color_patch(v):
      return True
  return False

def regional_to_ascii(cp):
  return unichr(ord('A') + cp - 0x1f1e6)

def is_flag_sequence(values):
  if len(values) != 2:
    return False
  for v in values:
    v -= 0x1f1e6
    if v < 0 or v > 25:
      return False
  return True

def is_keycap_sequence(values):
  return len(values) == 2 and values[1] == 0x20e3

def get_keycap_text(values):
  return '-%c-' % unichr(values[0]) # convert gags on '['

char_map = {
    0x1f468: 'M',
    0x1f469: 'W',
    0x1f466: 'B',
    0x1f467: 'G',
    0x2764: 'H', # heavy black heart, no var sel
    0x1f48b: 'K', # kiss mark
    0x200D: '-', # zwj placeholder
    0xfe0f: '-', # variation selector placeholder
    0x1f441: 'I', # Eye
    0x1f5e8: 'W', # 'witness' (left speech bubble)
}

def get_combining_text(values):
  chars = []
  for v in values:
    char = char_map.get(v, None)
    if not char:
      return None
    if char != '-':
      chars.append(char)
  return ''.join(chars)


if not path.isdir(OUTPUT_DIR):
  os.makedirs(OUTPUT_DIR)

with open('sequences.txt', 'r') as f:
  for seq in f:
    seq = seq.strip()
    text = None
    values = [int(code, 16) for code in seq.split('_')]
    if len(values) == 1:
      val = values[0]
      text = '%04X' % val # ensure upper case format
    elif is_flag_sequence(values):
      text = ''.join(regional_to_ascii(cp) for cp in values)
    elif has_color_patch(values):
      print('skipping color patch sequence %s' % seq)
    elif is_keycap_sequence(values):
      text = get_keycap_text(values)
    else:
      text = get_combining_text(values)
      if not text:
        print('missing %s' % seq)

    if text:
      if len(text) > 3:
        if len(text) == 4:
          hi = text[:2]
          lo = text[2:]
        else:
          hi = text[:-3]
          lo = text[-3:]
        text = '%s\n%s' % (hi, lo)
      generate_image('emoji_u%s.png' % seq, text)
