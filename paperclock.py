#!/usr/bin/env python3
# -*- coding:utf-8 -*-

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


from settings import Settings
from gpiozero import Button

import time
import datetime
import threading
import traceback

from display import Display
from openweathermap import OpenWeatherMap, Position
from intervals import repeating


def redraw_display(display):
    """Draws display"""
    display.show()

def get_forecast(display, openweathermap, settings):
    try:
        print('getting new forecast')
        weather = openweathermap.query(
            Position(settings.position['lat'], settings.position['lon']), settings.get('units', 'metric'))
        if weather is not None:
            display.update_weather(weather)
    except Exception as ex:
        print(f'Failed to update weather: {ex}')
        traceback.print_exc(ex)


@repeating(lambda: 120 - datetime.datetime.now().second)
def refresh_display(display):
    redraw_display(display)


@repeating(lambda: 15*60)
def update_weather(display, openweathermap, settings):
    get_forecast(display, openweathermap, settings)


def dummy_thread():
    while True:
        time.sleep(15)


if __name__ == '__main__':

    settings = Settings()

    display = Display(settings)
    weather = OpenWeatherMap(
        settings.openweathermap_api_key) if settings.openweathermap_api_key is not None else None
    get_forecast(display, weather, settings)

    refresh_display(display)
    update_weather(display, weather, settings)

    threading.Thread(target=dummy_thread).start()  # keep app alive
