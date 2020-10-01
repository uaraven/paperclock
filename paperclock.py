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


from PIL import ImageFont, Image, ImageDraw
from gpiozero import Button
from astral import Observer
from astral.geocoder import lookup, database
import time
import datetime
import json
import os
import threading
import waveshare_epd.epd2in7b as epd
from display import Display
from openweathermap import OpenWeatherMap, Position

eInk = epd.EPD()

time_formats = {'24h': '%H:%M', '12h': '%I:%M'}


class Context:
    # Buffers
    BLACK = 0
    RED = 1

    def __init__(self, eInk, config):
        self.config = config
        # horizontal display
        self.width = eInk.height
        self.height = eInk.width
        # Fonts
        self.big_font = ImageFont.FreeTypeFont(
            font='data/OpenSans-Bold.ttf', size=50)
        self.med_font = ImageFont.FreeTypeFont(
            font='data/OpenSans-SemiBold.ttf', size=20)
        self.small_font = ImageFont.FreeTypeFont(
            font='data/OpenSans-SemiBold.ttf', size=18)
        self.tiny_font = ImageFont.FreeTypeFont(
            font='data/OpenSans-SemiBold.ttf', size=14)

        # Icons
        self.sunrise = Image.open(
            'data/sunrise.png').convert(mode='1', dither=None)
        self.sunset = Image.open(
            'data/sunset.png').convert(mode='1', dither=None)

        # Date and time formats
        self.position = config['position']
        self.time_format = time_formats[config['time']
                                        ] if config['time'] in time_formats else time_formats['24h']
        self.time_format_tz = self.time_format + ' %Z'
        self.date_format = '%b %d, %Y'

        self.openweathermap = OpenWeatherMap(
            config.get('openweathermap_api_key', None))


def make_buffers():
    blackimage = Image.new('1', (eInk.height, eInk.width), 255)
    redimage = Image.new('1', (eInk.height, eInk.width), 255)
    drawblack = ImageDraw.Draw(blackimage)
    drawred = ImageDraw.Draw(redimage)

    return (drawblack, drawred, blackimage, redimage)


def show(buffers):
    eInk.init()
    eInk.display(eInk.getbuffer(
        buffers[2]), eInk.getbuffer(buffers[3]))
    eInk.sleep()


def redraw_display(clock_display, context):
    """Draws display"""
    buffers = make_buffers()
    clock_display.draw_display(buffers)

    show(buffers)


def timed_execution(clock_display, context):
    while True:
        redraw_display(clock_display, context)
        s_left = clock_display.refresh_time() - datetime.datetime.now().second
        time.sleep(s_left)


def update_weather(display, context):
    while True:
        try:
            weather = context.openweathermap.query(
                Position(context.position['lat'], context.position['lon']), context.config.get('units', 'metric'))
            if weather is not None:
                display.update_weather(weather)
        except Exception as ex:
            print(f'Failed to update weather: {ex}')
        time.sleep(15 * 60)


def post_process_config(config):
    if isinstance(config['location'], str):
        location = lookup(config['location'], database())
        position = {"lat": location.latitude, "lon": location.longitude}
    else:
        position = config['location']
    config['position'] = position
    return config


def load_config():
    if os.path.isfile('config.json'):
        name = 'config.json'
    else:
        name = os.path.join(os.environ.get('HOME'), '.paperclock')
    with open(name) as config:
        cnf = json.load(config)
        return post_process_config(cnf)


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

if __name__ == '__main__':
    try:
        config = load_config()
    except Exception as ex:
        print(f'Using default config: {ex}')
        config = default_config

    context = Context(eInk, config)

    display = Display(config, context)

    redraw_display(display, context)
    update_weather(display, context)

    clock_thread = threading.Thread(
        target=lambda: timed_execution(display, context))

    weather_thread = threading.Thread(
        target=lambda: update_weather(display, context))
    # wait till next minute
    s_left = 60 - datetime.datetime.now().second
    time.sleep(s_left)
    clock_thread.start()
