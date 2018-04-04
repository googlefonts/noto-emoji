# -*- coding: utf-8 -*-

import os
import sys
import argparse
from modifier import *
from emoji import *


def main():
    """
    Die main-Funktion, welche die Skin-Modifier verarbeitet
    :return: Nix
    """
    # Alle Kommandozeilenargumente hinzufügen
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required = True)
    group.add_argument('--input_file', '-i', help='Input file', metavar='ifile')
    group.add_argument('--input_dir', '-d', help='Input directory', metavar='idir', default = '.')
    parser.add_argument('--mod_dir', '-m', help='Modifier directory', metavar='mdir', default = './skins')
    parser.add_argument('--base_name', '-b', help='Name of the base skin color', metavar='bname', default='base')
    parser.add_argument('--add_end', '-e', help='Do you want to add an fe0f ZWJ-sequence?', default='n', choices=['y','n','auto'], required=False)
    # Zu dict verarbeiten
    args = vars(parser.parse_args())
    end = False if args['add_end'].lower() == 'n' else (True if args['add_end'].lower() == 'y' else None)
    # Skin-Modifier erstellen
    modifiers = generate_modifiers(args['mod_dir'])
    # Wurde ein Verzeichnis gewählt?
    if args['input_dir']:
        multi_process(args['input_dir'], modifiers, args['base_name'], end)
    else:
        # Erstelle ein Emoji-Objekt
        emoji = Emoji(modifiers, args['input_file'], args['base_name'], end)
        # Und wende die Modifier an
        emoji.batch_modify()


def generate_modifiers(path: str) -> dict:
    """
    Holt alle Skin-Modifier aus dem Ordner
    :param path: Der Ordner mit den JSON-Dateien
    :return: Ein dict mit name: Modifier
    """
    modifiers = {}
    for file in os.listdir(path):
        # Ist es überhaupt eine JSON-Datei?
        if os.path.splitext(file)[-1].lower() == '.json':
            # Erstelle aus der JSON-Datei und füge es ein
            modifier = Modifier.generate_from_json(os.path.join(path, file))
            modifiers.update({modifier.name: modifier})
    return modifiers


def multi_process(directory: str, modifiers: dict, base: str, end: bool = False):
    """
    Verarbeitet ein ganzes Verzeichnis mit Emojis
    :param directory: Der Ordner
    :param modifiers: Die Skin-Modifier
    :param base: Der Name des Basis-Typen
    :param end: Ob noch eine fe0f-Sequenz angefügt werden soll.
    :return: Nix
    """
    files = os.listdir(directory)
    for file in files:
        # Nur SVG wird derzeit unterstützt
        if os.path.splitext(file)[-1].lower() in {'.svg'}:
            # Erstelle ein Emoji-Objekt
            emoji = Emoji(modifiers, os.path.join(directory, file), base, end)
            # Und wende die Modifier an
            emoji.batch_modify()


if __name__ == '__main__':
    main()
