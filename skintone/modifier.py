import json
import os


class Modifier:
    """An Object containing all relevant information about one skin tone Modifier"""

    def __init__(self, name: str, colors: dict, extension: str, tolerance: int = 16, *args, **kwargs):
        """
        Creates a new skin tone modifier
        :param name: The name of this skin tone
        :param colors: All colors in 'name: color hex'-format
        :param extension: All characters to be added to the original emoji sequence (e.g. _200d_1f3b0)
        :param tolerance: The color 'radius' which is matched
        """
        self.name = name
        self.colors = colors
        self.extension = extension
        self.tolerance = tolerance

    def replace(self, colors, base) -> dict:
        """
        Creates a dict containing all color replacements
        :param colors: A dict containing the original color strings and their RGB values
        :param base: The base Modifier
        :return: A dict containing the replacement rules as from: to (they can be applied by using simple string substitution)
        """
        # Create a new list
        replace = list()
        # The base colors as a RGBA: hex string dict
        basecolors = Modifier.build_rgb(base)

        # Go through all the colors that have been found
        for old_color, value in colors.items():
            # ...And try to find a matching base color
            for base_value, color_name in basecolors.items():
                # Also match some surrounding colors
                if Modifier.eucl_dist(value, base_value) <= self.tolerance:
                    # It's a match!
                    try:
                        # Try to find an appropiate replacement
                        new_color = self.colors[color_name]
                        replace.append((old_color, new_color))
                    except KeyError:
                        try:
                            # We'll now try to ignore any extensions added with '_'
                            # (e.g. "hand_2" -> "hand", "skin_boo_ya" -> "skin")
                            new_color = self.colors[color_name.split('_')[0]]
                            replace.append((old_color, new_color))
                        except KeyError:
                            # Replacement not found
                            print('Didn\'t find replacement for color {} from {} (Name: "{}" or "{}") in {}.'.format(value, base.name, color, color.split('_')[0], self.name))  
        return dict(replace)

    @staticmethod
    def eucl_dist(a, b):
        """
        Returns the euclidean distance between two tuples
        :param a: The first tuple
        :param b: The second tuple
        :return: Their euclidean distance
        """
        pairs = zip(a,b)
        dist = map(lambda x: (x[0]-x[1])**2, pairs)
        return sum(dist)**(1/2)

    def build_rgb(self) -> dict:
        """
        Returns the colors dict with the RGBA values as a tuple instead of a hex string and with the colors as keys
        :return: A dict with RGBA tuple:color name
        """
        colors = list()
        for name, value in self.colors.items():
            # Get rid of the #
            value = value.replace('#','').strip()
            value = [value[0:2], value[2:4], value[4:6], value[6:8]]
            # Add an alpha value if necessary
            if not value[3]:
                value[3] = 'ff'
            value = tuple(int(v, 16) for v in value)
            colors.append((value, name))
        return dict(colors)

    @staticmethod
    def generate_from_json(file: str):
        """
        Creates a new Modifier object out of a JSON file
        :param file: The file path
        :return: A new Modifier parsed from this JSON file
        """
        try:
            # Open file
            with open(file) as json_file:
                # Load JSON table
                jdict = json.loads(json_file.read())
                # Do we have a name?
                if 'name' in jdict:
                    return Modifier(**jdict)
                else:
                    # If not, we'll just use the file name
                    return Modifier(name= os.path.splitext(os.path.basename(file))[0], **jdict)
        except FileNotFoundError:
            print("File not found  ¯\_(ツ)_/¯")
        except json.JSONDecodeError:
            print("This is not a valid JSON file >:(")

    def __str__(self):
        return '{} (uxxxx_{}): Skin tone modifier with {} different colors'.format(self.name, self.extension, len(self.colors))

    def detailed_info(self) -> str:
        """
        Returns more detailed information on this Modifier 
        :return: A str containing some details
        """
        return '{} (uxxxx_{}):\n    {}'.format(self.name, self.extension, '\n    '.join([': '.join(item) for item in list(self.colors.items())]))


class HexString:
    """
    This is a simple data type to handle conversions and some basic operations on hexadecimal strings.
    """

    def __init__(self, string: str, min_: int = 0, max_: int = 0xff, length: int = 2):
        """
        Create a new HexString
        :param string: The string representation without the 0x-prefix
        :param min_: The min allowed value
        :param max_: The max allowed value
        :param length: The max zfill length
        """
        self.string = string.zfill(length)
        self.value = int(string, 16)
        self.min_ = min_
        self.max_ = max_
        self.length = length

    def __add__(self, other):
        """
        Add another HexString or int
        :param other: summand
        :return: A new HexString with this operation applied
        """
        if type(other) == int:
            # Add
            result = HexString(hex(self.value + other)[2:], self.min_, self.max_)
            # Test for range
            if result.value in range(self.min_, self.max_ + 1):
                return result
            else:
                raise ValueError('Value not in allowed range')
        if type(other) == HexString:
            # Add
            result = HexString(hex(self.value + other.value)[2:], self.min_, self.max_)
            # Test for range
            if result.value in range(self.min_, self.max_ + 1):
                return result
            else:
                raise ValueError('Value not in allowed range')

    def __sub__(self, other):
        """
        Sub another HexString or int
        :param other: Subtrahend
        :return: A new HexString with this operation applied
        """
        if type(other) == int:
            # Sub
            result = HexString(hex(self.value - other)[2:], self.min_, self.max_)
            # Test for range
            if result.value in range(self.min_, self.max_ + 1):
                return result
            else:
                raise ValueError('Value not in allowed range')
        if type(other) == HexString:
            # Sub
            result = HexString(hex(self.value - other.value)[2:], self.min_, self.max_)
            # Test for range
            if result.value in range(self.min_, self.max_ + 1):
                return result
            else:
                raise ValueError('Value not in allowed range')

    def __mul__(self, other):
        result = HexString(hex(self.value * other)[2:], self.min_, self.max_)
        # Test for range
        if result.value in range(self.min_, self.max_ + 1):
            return result
        else:
            raise ValueError('Value not in allowed range')

    def __len__(self):
        return self.length

    def __str__(self):
        return self.string.zfill(self.length)
