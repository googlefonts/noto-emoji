from modifier import *
import re


class Emoji:

    # There are some cases where an FE0F character has to be applied. 
    # This is the case for gender symbols which should be represented as emojis and not as characters
    fe0f_chars = {'♀', '♂'}

    color_regex = re.compile("#([a-f0-9]{6,7})|rgb\(([0-9]{1,3},[0-9]{1,3},[0-9]{1,3})\)", re.IGNORECASE)

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
                print('{} applied to Emoji {}.'.format(name, self.name))

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
        content = self.content
        colors = self.get_colors()
        modifications = modifier.replace(colors, self.base)

        # All colors to be replaced are indexed by their original string. We'll replace one by one
        for old, new in modifications.items():
            content = content.replace(old, new)
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
        
    def get_colors(self) -> dict:
        """
        Extracts all color values and their corresponding strings
        :return: A dict containing actually used color strings as keys and their RGBA values as values (i.e. '#ff0000': (255,0,0,0))
        """
        colors = list()
        results = Emoji.color_regex.finditer(self.content)

        for result in results:
            index = result.group(0)
            if result.group(1):
                # Hexadecimal
                value = result.group(1)
                value = [value[0:2], value[2:4], value[4:6], value[6:8]]
                # Add an alpha value if necessary
                if not value[3]:
                    value[3] = 'ff'
                value = tuple(int(v, 16) for v in value)
            elif result.group(2):
                # RGB notation
                value = result.group(2)
                value = value.split(',')
                value = tuple(map(int, value))
            else:
                # This cannot happen since it has either to be a hex string or in rgb notation
                raise ValueError()
            colors.append((index, value))

        return dict(colors)

            
