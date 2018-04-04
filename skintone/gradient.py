from modifier import HexString
import re


class Gradient:
    """
    Ein Farbverlauf mit verschiedenen Stops
    """
    def __init__(self, stops: list, raw: str):
        """
        Erstelle einen neuen Farbverlauf
        :param stops: Die einzelnen Stops
        :param raw: Der ursprüngliche String
        """
        self.stops = stops
        self.raw = raw

    def calculate_average(self) -> str:
        """
        Berechnet die durchschnittliche Farbe mit Berücksichtigung der Offsets
        :return: Die Farbe als String
        """
        # Platzhalter
        av_color = []
        colors = []
        # Gehe jeden Stop durch
        for stop in self.stops:
            # Hole die einzelnen Farbkomponenten
            components = stop.components
            for i, component in enumerate(components):
                # Hole die Länge/Breite ab
                length = stop.length()
                # Und berechne die Gewichtung
                components[i] = length * component.value
            colors.append(components)
        # Jetzt sind die Komponenten wichtig
        for component in zip(*colors):
            av_color.append(HexString(hex(round(sum(component)))[2:]))
        # Zum String machen
        return '#' + ''.join([str(component) for component in av_color])

    def first_color(self) -> str:
        return self.stops[0].color

    @staticmethod
    def from_xml(in_str: str) -> list:
        """
        Erstelle Farbverläufe aus einem XML-String
        :param in_str: Die XML-Datei als String
        :return: Dei Farbverläufe als Liste
        """
        # Erstellt den reg. Ausdruck
        regex = re.compile(r'(<[a-z]*Gradient .*>)((.|\n)+)(</[a-z]*Gradient>)', re.IGNORECASE)
        # Sucht alle Farbverläufe raus
        results = regex.findall(in_str)
        resulting_gradients = []
        # Erstellt die Objekte
        for result in results:
            stops = Stop.from_xml(result[1])
            resulting_gradients.append(Gradient(stops, ''.join(result)))
        return resulting_gradients

    def replace_stops(self) -> str:
        """
        Ersetzt die Farben der Stops durch den Durchschnitt
        :return: Der XML-String mit den Änderungen
        """
        regex = re.compile(r'<stop offset="((\.|[0-9])*)" style="stop-color:(#[1-9,A-F]*)"/>')
        return regex.sub(r'<stop offset="\1" style="stop-color:{}"/>'.format(self.first_color().upper()), self.raw)

    def __str__(self):
        return 'Farbverlauf mit {} Stops'.format(len(self.stops))

    def __getitem__(self, key):
        return self.stops[key]


class Stop:
    def __init__(self, offset: float, color: str, next_: float, prev: float):
        """
        Erstellt einen neuen Stop im Farbverlauf
        :param offset: Die Position
        :param color: Die Farbe als Hex-String
        :param next_: Die nächste Position
        :param prev: Die vorherige Position
        """
        self.next = next_
        self.prev = prev
        self.offset = offset
        self.color = color

    def __str__(self):
        return 'Stop @ {}, Color: {}'.format(self.offset, self.color)

    @property
    def components(self) -> list:
        """
        Gibt die Komponenten als HexString aus
        :return: Eine Liste von HexStrings (3 Stück; RGB)
        """
        if len(self.color) == 7: # Gibt nur RGB
            return [HexString(self.color[1:3]), HexString(self.color[3:5]), HexString(self.color[5:7])]

    @components.setter
    def components(self, values):
        self.color = '#' + ''.join(values)

    def __len__(self) -> int:
        """
        Gibt an, wie breit der Streifen ist (als int, was i.d.R 0 ist)
        :return: Die Breite als int
        """
        upper_ = (self.next + self.offset) // 2 # prev-------self---|---next
        lower_ = (self.prev + self.offset) // 2 # prev---|---self-------next
        return int(abs(upper_ - lower_))

    def length(self) -> float:
        """
        Gibt die Breite des Streifens mit dieser Farbe zurück
        :return: Die Breite als float
        """
        upper_ = (self.next + self.offset) / 2 # prev-------self---|---next
        lower_ = (self.prev + self.offset) / 2 # prev---|---self-------next
        return abs(upper_ - lower_)            # prev---|==========|---next

    @staticmethod
    def from_xml(in_str: str) -> list:
        """
        Erstellt Stops aus einem XML-String
        :param in_str: Der String
        :return: Eine Liste mit Stop-Objekten
        """
        # reg. Ausdruck erstellen
        regex = re.compile(r"""<stop offset="((\.|[0-9])*)" style="stop-color:(#[1-9,A-F]*)"/>""", re.IGNORECASE)
        results = regex.findall(in_str)
        stops = []
        # Parse die Resultate
        for i, result in enumerate(results):
            # Gibt es einen vorherigen Stop?
            if i > 0:
                prev = results[i-1][0]
            else:
                prev = 0
            # Gibt es einen nachfolgenden Stop?
            if i < len(results) - 1:
                next_ = results[i+1][0]
            else:
                next_ = 1
            # Das Muster ist: <stop offset="{0}" style="stop-color:{2}"/>
            stops.append(Stop(float(result[0]), result[2], float(prev), float(next_)))
        return stops