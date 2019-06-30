import os
import ConfigParser

from seemmo.common.paths import script_path

class Config:
    def __init__(self, filename, section='global'):
        self.section = section
        self.filepath = os.path.join(script_path, 'conf', filename)
        self.parser, self.properties = self._load(self.filepath, section)

    @staticmethod
    def _load(filepath, section):
        parser = ConfigParser.ConfigParser()
        parser.read(filepath)
        if section not in parser.sections():
            parser.add_section(section)
        properties = {}
        for key in parser.options(section):
            properties[key] = parser.get(section, key)
        return parser, properties

    def get(self, key, default=None):
        return self.properties.get(key, default)

    def set(self, key, value):
        self.properties[key] = value

    def save(self):
        for key, value in self.properties.items():
            self.parser.set(self.section, key, value)
        with open(self.filepath, 'w') as configfile:
            self.parser.write(configfile)

    def clean(self):
        os.remove(self.filepath)

