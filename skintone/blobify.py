import generate_skincolor
import remove_gradient
import emoji
import argparse
import os


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
    parser.add_argument('--mod_dir', '-m', help='Modifier directory', metavar='mdir', default = './blob')
    parser.add_argument('--base_name', '-b', help='Name of the base skin color', metavar='bname', default='base')
    # Zu dict verarbeiten
    args = vars(parser.parse_args())
    # SKin-Modifier erstellen
    modifiers = generate_skincolor.generate_modifiers(args['mod_dir'])
    # Wurde ein Verzeichnis gewählt?
    if args['input_dir']:
        process_folder(args['input_dir'], modifiers, args['base_name'])
    else:
        process_file(modifiers, modifiers, args['base_name'])


def process_folder(path: str, modifiers, base) -> None:
    """
    Entfernt die Verläufe für alle Dateien eines Ordners
    :param path: Der Pfad zur Datei
    :param modifiers: Die Modifikatoren
    :param base: Der Basistyp
    :return: Nix (ändert die Datei)
    """
    files = os.listdir(path)
    errors = []
    for file in files:
        # Nur SVG wird derzeit unterstützt
        if os.path.splitext(file)[-1].lower() in {'.svg'}:
            err = process_file(os.path.join(path, file), modifiers, base, True)
            if err:
                errors.append(err)
    print('Es sind {} Fehler aufgetreten bei folgenden Dateien:\n    {}'.format(len(errors), '\n    '.join(errors)))


def process_file(path, modifiers, base, folder = False):
    try:
        # Entferne Verläufe
        remove_gradient.process_file(path)
        # Erstelle ein Emoji-Objekt
        emoji_ = emoji.Emoji(modifiers, path, base)
        # Und wende die Modifier an
        emoji_.batch_modify()
    except Exception as e:
        print('Es ist ein Fehler aufgetreten beim Bearbeiten von: {}'.format(path))
        print(e)
        return path


if __name__ == '__main__':
    main()