import argparse
from gradient import *
import os


def main():
    """
    Die main-Funktion, welche die Farbverläufe entfernt
    :return: Nix
    """
    # Alle Kommandozeilenargumente hinzufügen
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required = True)
    group.add_argument('--input_file', '-i', help='Input file', metavar='ifile')
    group.add_argument('--input_dir', '-d', help='Input directory', metavar='idir', default = '.')
    # Zu dict verarbeiten
    args = vars(parser.parse_args())
    if args['input_dir']:
        process_folder(args['input_dir'])
    else:
        process_file(args['input_file'])


def process_file(path: str) -> None:
    """
    Entfernt die Verläufe
    :param path: Der Pfad zur Datei
    :return: Nix (ändert die Datei)
    """
    with open(path, 'r') as file:
        text = file.read()
        # Erstelle den Reg. Ausdruck
        regex = re.compile(
            r'(<(linear|radial)Gradient .*>)(( |\n)*)(<stop.*>)(( |\n)*<stop.*>)*(( |\n)*)(</(linear|radial)Gradient>)',
            re.IGNORECASE)
        text = regex.sub(r'\1\3\5\8\10', text)
    with open(path, 'w') as file:
        file.seek(0)
        file.truncate()
        file.write(text)


def process_folder(path: str) -> None:
    """
    Entfernt die Verläufe für alle Dateien eines Ordners
    :param path: Der Pfad zur Datei
    :return: Nix (ändert die Datei)
    """
    files = os.listdir(path)
    for file in files:
        # Nur SVG wird derzeit unterstützt
        if os.path.splitext(file)[-1].lower() in {'.svg'}:
            print(path)
            print(os.path.join(path, file))
            process_file(os.path.join(path, file))


if __name__ == '__main__':
    main()

