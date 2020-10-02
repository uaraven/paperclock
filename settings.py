# Copyright 2020 Oleksiy Voronin
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import json
import os
from astral.geocoder import lookup, database


class Settings:

    default_config = {
        "location": {
            'lat': 0.0,
            'lon': 0.0
        },
        "secondTZ": "UTC",
        "openweathermap_api_key": None,
        "units": "metric",
        "time": "24h"
    }

    time_formats = {'24h': '%H:%M', '12h': '%I:%M'}

    def __init__(self):
        try:
            config = self._load_config()
        except Exception as ex:
            print(f'Using default config: {ex}')
            config = self.default_config

        self.config = config

        if isinstance(config['location'], str):
            location = lookup(config['location'], database())
            position = {"lat": location.latitude, "lon": location.longitude}
        else:
            position = config['location']
        self.position = position

        # Date and time formats
        self.time_format = self.time_formats[config['time']]\
            if config['time'] in self.time_formats else self.time_formats['24h']
        self.time_format_tz = self.time_format + ' %Z'
        self.date_format = '%b %d, %Y'

        # self.openweathermap = OpenWeatherMap(
        #     config.get('openweathermap_api_key', None))

    def _load_config(self):
        if os.path.isfile('config.json'):
            name = 'config.json'
        else:
            name = os.path.join(os.environ.get('HOME'), '.paperclock')
        with open(name) as config:
            cnf = json.load(config)
            return cnf

    def get(self, name, default):
        return self.config.get(name, default)

    def __getattr__(self, name):
        return self.config.get(name, None)
