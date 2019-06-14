#!/usr/bin/env python
#
# Copyright (C) 2018 Constantin A.
#
# Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import os
import sys

# That's what we'd like to insert in our CHANGES.md later
pattern = "\n| ![&#x{0};](https://rawgit.com/googlei18n/noto-emoji/e456654119cc3a5f9bebb7bbd00512456f983d2d/png/128/emoji_u{0}.png) | ![&#x{0};](http://rawgit.com/C1710/blobmoji/master/png/128/emoji_u{0}.png)	| U+{0}	| {1}	| {2}	|  "

def get_sequences() -> list:
    """Get the codepoints from the command line input"""
    sequences = []
    add = ''
    print('Please enter all sequences that you\'d like to add. Undo with \'u\', finish with \'e\':')
    while add.lower() != 'e':
        add = input()
        if add.lower() == 'u':
            rm = sequences[-1]
            sequences = sequences[:-1]
            print('"{}" Removed'.format(rm))
        elif add.lower() != 'e' and add != '':
            sequences.append(add)
    return sequences

def get_details(sequences: list) -> list:
    details = []
    print('Please enter the type of change and (maybe) a small comment.')
    print("""The Default types are:\n
      n  - new\n
      n* - new*\n
      g  - goo\n
      a  - alt\n
    Shortcuts will simply be replaced. If you don't want them to be replaced, place a '\\' in front of it""")
    print('You can undo your last step if you type \'u\'\n')

    for seq in sequences:
        print(seq)
        type_, comment = 'u','u'
        while type_.lower() == 'u':
            type_ = input('  Type: ')
        if type_[0] != '\\':
            type_ = type_.replace('n', 'new').replace('g', 'goo').replace('a', 'alt')
        while comment.lower() == 'u':
            comment = input('  Comment: ')
        details.append((seq, type_, comment))
    return details

def produce_strings(details: list) -> list:
    lines = []
    for name, type_, comment in details:
        lines.append(pattern.format(name, type_, comment))
    return lines

def review(details: list) -> bool:
    print('Please review the sequences before overwriting the CHANGES.md-file:')
    for detail in details:
        print('U+{0}: {1} \t-\t "{2}"'.format(*detail))
    descision = ''
    while not descision.lower() in ('n', 'y'):
        descision = input('Are you sure you want to add these? [y/n]: ')
    return descision.lower() == 'y'

def seq_from_file(filename: str) -> list:
    with open(filename) as file:
        if not '#' in file.read(128):
            file.seek(0)
            return file.readlines()
        else:
            file.seek(0)
            return seq_from_unicode(file)


def seq_from_unicode(file) -> list:
    sequences = []
    # Read all the lines
    for line in file:
        # Remove comments and any other information that is not needed
        line = line.split('#')[0].strip()
        line = line.split(';')[0].strip()
        # Is there any content left?
        if len(line):
            # Handle sequences
            sequence = line.split(' ')
            sequence = [c.strip() for c in sequence if len(c.strip())]
            if len(sequence) == 1:
                # Handle ranges
                codepoints = sequence[0].split('..')
                codepoints = [int(x, base=16) for x in codepoints]
                if len(codepoints) == 2:
                    for i in range(codepoints[0], codepoints[1]+1):
                        sequences.append(hex(i)[2:])
                else:
                    # Handle single codepoints
                    sequences.append(hex(codepoints[0])[2:])
            else:
                sequences.append('_'.join(sequence).lower())
    return sequences


path = 'CHANGES.md'

def write(strings: list):
    with open(path, mode='a') as md_file:
        for line in strings:
            	md_file.write(line)

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        sequences = get_sequences()
    else:
        sequences = []
        for f in sys.argv[1:]:
            sequences.extend(seq_from_file(sys.argv[1]))
    
    # remove duplicates
    sequences = list(dict.fromkeys(sequences))
    details = get_details(sequences)
    if review(details):
        write(produce_strings(details))