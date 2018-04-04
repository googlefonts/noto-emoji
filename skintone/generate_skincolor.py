# -*- coding: utf-8 -*-

import os
import sys
import argparse
from modifier import *
from emoji import *


def main():
    """
    The main function doing all the work
    :return: Nothing
    """
    # We'll need all those command line arguments
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required = True)
    group.add_argument('--input_file', '-i', help='Input file.svg', metavar='ifile')
    group.add_argument('--input_dir', '-d', help='Directory containing all base files.svg', metavar='idir', default = '.')
    parser.add_argument('--mod_dir', '-m', help='Directory containing all modifier.json', metavar='mdir', default = './skins')
    parser.add_argument('--base_name', '-b', help='Name of the base skin color (without file extensions)', metavar='bname', default='base')
    parser.add_argument('--add_end', '-e', help='Do you want to add an fe0f ZWJ-sequence?', default='auto', choices=['y','n','auto'], required=False)
    # Make a dict out of it
    args = vars(parser.parse_args())
    end = False if args['add_end'].lower() == 'n' else (True if args['add_end'].lower() == 'y' else None)
    # Create skin-Modifiers
    modifiers = generate_modifiers(args['mod_dir'])
    # Did the user chose a dir or a file?
    if args['input_dir']:
        multi_process(args['input_dir'], modifiers, args['base_name'], end)
    else:
        # Create this one Emoji object
        emoji = Emoji(modifiers, args['input_file'], args['base_name'], end)
        # Apply modifiers
        emoji.batch_modify()


def generate_modifiers(path: str) -> dict:
    """
    Parses all skin modifiers in their directory
    :param path: Directory containing the JSON files for the modifiers
    :return: A str-Modifier dict containing the modifiers, sorted by their name (name: modifier)
    """
    modifiers = {}
    for file in os.listdir(path):
        # Ignore non-JSON files
        if os.path.splitext(file)[-1].lower() == '.json':
            # Create one Modifier out of this JSON file
            modifier = Modifier.generate_from_json(os.path.join(path, file))
            modifiers.update({modifier.name: modifier})
    return modifiers


def multi_process(directory: str, modifiers: dict, base: str, end: bool = False):
    """
    Processes one directory of Emoji files
    :param directory: The directory containing the base SVG files
    :param modifiers: All Modifiers (probably provided by generate_modifiers)
    :param base: The name of the base skin color used in the base SVG files
    :param end: If an FE0F sequence should be added
    :return: Nothing (Files will be written)
    """
    files = os.listdir(directory)
    for file in files:
        # Ignore non-SVG-files
        if os.path.splitext(file)[-1].lower() in {'.svg'}:
            # Create a new Emoji-object
            emoji = Emoji(modifiers, os.path.join(directory, file), base, end)
            # Apply modifiers
            emoji.batch_modify()


if __name__ == '__main__':
    main()
