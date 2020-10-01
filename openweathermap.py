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

import requests
import datetime


def get_s(key, json, default=None):
    """Safe get from json"""
    return json.get(key, default)


def get_f(key, json, func, default=None):
    """Safe get from json and apply func to the value"""
    return func(json[key]) if key in json else default


class Position:
    def __init__(self, lat, lon) -> None:
        self.lat = lat
        self.lon = lon


class Weather:
    def __init__(self, json) -> None:
        self.id = json['id']
        self.name = json['main']
        self.description = json['description']
        self.icon = json['icon']


class MinutelyPrecipitation:
    def __init__(self, json) -> None:
        self.time = datetime.datetime.fromtimestamp(json['dt'])
        self.precipitation = json['precipitation']


class DailyForecast:
    def __init__(self, json) -> None:
        self.time = datetime.datetime.fromtimestamp(json['dt'])
        self.sunrise = get_f('sunrise', json, datetime.datetime.fromtimestamp)
        self.sunset = get_f('sunset', json, datetime.datetime.fromtimestamp)
        self.temperatures = json['temp']
        self.feels_like = get_s('feels_like', json)
        self.pressure = json['pressure']
        self.humidity = json['humidity']
        self.dew_point = get_s('dew_point', json)
        self.uvi = get_s('uvi', json)
        self.clouds = json['clouds']
        self.visibility = json['visibility']
        self.wind_speed = json['wind_speed']
        self.wind_direction = json['wind_deg']
        self.wind_gust = json['wind_gust'] if 'wind_gust' in json else None
        self.weather = [Weather(w) for w in get_s('weather', json, [])]
        self.rain = get_s('rain', json)
        self.pop = get_s('pop', json)


class Alert:
    def __init__(self, json) -> None:
        self.authority = get_s('sender_name', json, '')
        self.event = json['event']
        self.start = datetime.datetime.fromtimestamp(json['start'])
        self.end = datetime.datetime.fromtimestamp(json['end'])
        self.description = get_s('description', json, '')


class WeatherDataPoint:
    def __init__(self, json) -> None:
        self.time = datetime.datetime.fromtimestamp(json['dt'])
        self.sunrise = get_f('sunrise', json, datetime.datetime.fromtimestamp)
        self.sunset = get_f('sunset', json, datetime.datetime.fromtimestamp)
        self.temperature = json['temp']
        self.feels_like = get_s('feels_like', json)
        self.pressure = json['pressure']
        self.humidity = json['humidity']
        self.dew_point = get_s('dew_point', json)
        self.uvi = get_s('uvi', json)
        self.clouds = json['clouds']
        self.visibility = json['visibility']
        self.wind_speed = json['wind_speed']
        self.wind_direction = json['wind_deg']
        self.wind_gust = get_s('wind_gust', json)
        self.rain = get_s('rain', json)
        self.pop = get_s('pop', json)

        self.weather = [Weather(w) for w in get_s('weather', json, [])]
        self.hourly = [WeatherDataPoint(h) for h in get_s('hourly', json, [])]
        self.daily = [DailyForecast(d) for d in get_s('daily', json, [])]
        self.alerts = [Alert(a)for a in get_s('alerts', json, [])]


class WeatherInfo:
    def __init__(self, json):
        current = json['current']
        self.current = WeatherDataPoint(current)
        self.minutely_precipitation = [
            MinutelyPrecipitation(m) for m in json['minutely']]


class OpenWeatherMap:
    BASE_URL = 'https://api.openweathermap.org/data/2.5/onecall'

    def __init__(self, api_key):
        self.api_key = api_key

    def query(self, position: Position, units='metric', **kwargs):
        params = {
            'lon': position.lon,
            'lat': position.lat,
            'units': units,
        }
        if self.api_key is not None:
            params['appid'] = self.api_key
        for k, v in kwargs.items():
            params[k] = v

        response = requests.get(self.BASE_URL, params=params)
        if response.status_code != 200:
            raise Exception(
                f'Error calling OpenWeatherMap API. Status: {response.status_code} {response.reason}, Message: {response.text}')

        return WeatherInfo(response.json())


if __name__ == '__main__':

    map = OpenWeatherMap('887daf92380a199c6c3bb477121255b2')
    weather = map.query(Position(43.631389,  -80.038889))
    print(weather)
