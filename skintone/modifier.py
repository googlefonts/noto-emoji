import json
import os


class Modifier:
    """An Object containing all relevant information about one skin tone Modifier"""

    def __init__(self, name: str, colors: dict, extension: str, tolerance: int = 2, *args, **kwargs):
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

    def replace(self, base) -> dict:
        """
        Creates a dict containing all replacements
        :param base: The base Modifier
        :return: A dict containing the replacement rules as regular expressions
        (e.g.: {'#(00|01|02)(00|01|02)(00|01|02)': '#ffffff', '#(10|11|12|13|14)(32|33|34|35|36)(54|55|56|57|58)': '#28923'}
        """
        # Create a new dict
        replace = dict()
        # Color: The color's name (e.g. 'skin')
        # Value: The actual color code
        for color, value in base.colors.items():
            try:
                # Try to find an appropiate replacement
                replace.update({base.generate_tolerance(value): self.colors[color]})
            except KeyError:
                try:
                    # We'll now try to ignore any extensions added with '_'
                    # (e.g. "hand_2" -> "hand", "skin_boo_ya" -> "skin")
                    replace.update({base.generate_tolerance(value): self.colors[color.split('_')[0]]})
                except KeyError:
                    # Replacement not found
                    print('Didn\'t find replacement for color {} from {} (Name: "{}" or "{}") in {}.'.format(value, base.name, color, color.split('_')[0], self.name))
        return replace

    def generate_tolerance(self, val: str) -> str:
        """
        Generates a color radius to get a little tolerance
        Please note this is really bad code. 
        Even in comparison to the rest of this crap.
        :param val: The color's hex code (e.g. #12345D)
        :return: a regular expression covering this radius (e.g: #(10|11|12|13|14)(32|33|34|35|36)(5B|5C|5D|5E|5F))
        """
        if len(val) == 7: # RGB
            pairs = [val[1:3], val[3:5], val[5:7]]
        else: # RGBA
            pairs = [val[1:3], val[3:5], val[5:7], val[7:9]]
        # Placeholder for the new color components
        new_pairs = []
        for pair in pairs:
            # Create a new Hex String with the two digits
            hex = HexString(pair, 0, 0xff, 2)
            # This one will contain all variations
            # (42 will become [40,41,42,43,44])
            vals = []
            # Go through all possible values
            for plus in range(-self.tolerance, self.tolerance + 1):
                try:
                    # Try to add an offset
                    vals.append(hex + plus)
                except ValueError: 
                    # Ignore if the maximum range is exceeded
                    pass
            # Apply the new values
            new_pairs.append('({})'.format('|'.join((str(val) for val in vals))))
        return '#' + ''.join(new_pairs)

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
