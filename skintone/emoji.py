from modifier import *
import re


class Emoji:

    # There are some cases where an FE0F character has to be applied. 
    # This is the case for gender symbols which should be represented as emojis and not as characters
    fe0f_chars = {'♀', '♂'}

    def __init__(self, modifiers: dict, path: str, base: str, end: bool = False):
        """
        Create a new Emoji
        :param modifiers: All skin modifiers available to this emoji
        :param path: The path of the base SVG file
        :param base: Name of the base type
        :param end: True/False explicitly sets the FE0F character. fe0f_chars is used if None
        """
        # Assignments
        self.modifiers = modifiers
        self.path = path
        self.directory = os.path.dirname(path)
        self.base = modifiers[base]
        self.name = os.path.splitext(os.path.basename(path))[0]
        self.fextension = os.path.splitext(os.path.basename(path))[1]
        self.content = self.load()
        if end is not None:
            # Explicit
            self.end = end
        else:
            # Implicit
            self.end = False
            # Does it contain an "FE0F indicator"?
            for char in Emoji.fe0f_chars:
                if(char in path):
                    self.end = True
                    break

    def batch_modify(self):
        """
        new_modified_file for all Modifiers
        :return: None
        """
        for name, modifier in self.modifiers.items():
            # You don't need to convert from base to base
            if modifier != self.base:
                self.new_modified_file(modifier)
                print('{} auf Emoji {} angewendet.'.format(name, self.name))

    def new_modified_file(self, modifier: Modifier):
        """
        Creates a new skin tone variant file
        :param modifier: The Modifier
        :return: None
        """
        # Update the SVG file
        new_content = self.generate_modified(modifier)
        # Save file
        self.save(new_content, modifier.extension)

    def load(self) -> str:
        """Gets the (text) content of the base SVG file of this Emoji.
        :return: the SVG file's content"""
        try:
            with open(self.path) as file:
                return file.read()
        except FileNotFoundError:
            print('File "{}" not found!'.format(self.path))

    def generate_modified(self, modifier: Modifier):
        """
        Creates a new skin tone variant of this Emoji
        :param modifier: The Modifier which has to be applied
        :return: The altered SVG file's content
        """
        # We're going to work on a copy of the content
        content = self.content
        # All colors are indexed by their name. We'll replace one by one
        for old, new in modifier.replace(self.base).items():
            # Create the regular expression which will be used
            old_regex = re.compile(old, re.IGNORECASE)
            # ...Apply it
            content = old_regex.sub(new, content)
        return content

    def save(self, content: str, extension: str) -> None:
        """
        Save the new skin tone variant
        :param content: The new content which has been created
        :param extension: Any new characters which have to be added (usually 200d + the skin tone modifier)
        :return: None (writes the file)
        """
        # Well, this should be obvious...
        with open(self.generate_path(extension), 'w') as file:
            file.write(content)

    def generate_path(self, extension: str) -> str:
        """
        Creates the file path of the newly created variant
        :param extension: All characters which have to be added to this emoji.
        :return: A str containing the path/to/emoji_variant.svg
        """
        # Which directory? (It will be saved in the same one as the base emoji)
        directory = self.directory
        # Which is the base name of the file? (e.g. emoji_u1f973)
        basename = self.name
        # The file extension (.svg)
        fileextension = self.fextension
        base_seq = basename.split('_')
        base_seq.insert(2, extension)
        # Add FE0F?
        if self.end:
            base_seq.append('fe0f')
        basename = '_'.join(base_seq)
        # Stitch it together and return the whole file path
        return os.path.join(directory, basename) + fileextension
