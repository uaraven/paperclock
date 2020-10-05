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

from display import Display, Layout
from openweathermap import OpenWeatherMap, Position
from intervals import repeating


class Controller:
    def __init__(self, settings: Settings):
        display = Display(settings)

        self.button1 = Button(5)
        self.button2 = Button(6)
        self.button3 = Button(13)
        self.button4 = Button(19)

        self.button1.when_pressed = self.button1pressed

        self.settings = settings
        self.layout = Layout(display, settings)
        if settings.openweathermap_api_key is not None:
            self.openweathermap = OpenWeatherMap(
                settings.openweathermap_api_key)
            self.get_forecast()

    def run(self):
        self.refresh_display()
        self.update_weather()

        def dummy_thread():
            while True:
                time.sleep(15)

        threading.Thread(target=dummy_thread).start()  # keep app alive

    def button1pressed(self):
        print("button 1 pressed")
        self.layout.weather.set_state(self.layout.weather.CURRENT_DETAILS)
        self.layout.draw()

    def get_forecast(self):
        try:
            print('getting new forecast')
            weather = self.openweathermap.query(
                Position(self.settings.position['lat'], self.settings.position['lon']), self.settings.get('units', 'metric'))
            if weather is not None:
                self.layout.weather.update(weather)
        except Exception as ex:
            print(f'Failed to update weather: {ex}')
            traceback.print_exc(ex)

    def redraw_display(self):
        """Draws display"""
        self.layout.draw()

    @repeating(lambda: 120 - datetime.datetime.now().second)
    def refresh_display(self):
        self.redraw_display()

    @repeating(lambda: 15*60)
    def update_weather(self):
        self.get_forecast()


if __name__ == '__main__':

    controller = Controller(Settings())

    controller.run()
