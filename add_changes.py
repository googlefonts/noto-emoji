import os

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

path = 'CHANGES.md'

def write(strings: list):
    with open(path, mode='a') as md_file:
        for line in strings:
            	md_file.write(line)

if __name__ == '__main__':
    details = get_details(get_sequences())
    if review(details):
        write(produce_strings(details))