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

import time
import datetime
from pytz import timezone
from dateutil.tz import tzlocal
from PIL import Image, ImageDraw, ImageFont
from astral import Observer
from astral.geocoder import lookup, database
from astral.sun import sun
import math

DEBUG_CENTER_BOUNDS = False


class BaseDisplay:
    def __init__(self, config, context):
        self.config = config
        self.context = context
        self.buffers = []

    def draw_text(self, xy, text, font, buffer_id):
        self.buffers[buffer_id].text(
            xy, text, font=font, fill=0)

    def draw_text_centered(self, xy, w, text, font, buffer_id):
        """xy - top left coordinates of the bounding box
          w - width of the bounding box

          Text will be horizontally centered in the bounding box"""
        tsize = self.buffers[buffer_id].textsize(
            text, font=font)
        x = (w - tsize[0]) / 2

        self.buffers[buffer_id].text(
            (xy[0] + x, xy[1]), text, font=font, fill=0)

        if DEBUG_CENTER_BOUNDS:
            self.buffers[buffer_id].line([xy, (xy[0], xy[1] + tsize[1])])
            self.buffers[buffer_id].line(
                [(xy[0] + w, xy[1]), (xy[0] + w, xy[1] + tsize[1])])

    def draw_image(self, xy, image, buffer_id=0):
        self.buffers[buffer_id + 2].paste(image, xy)

    def draw_icon_text_centered(self, pos, width, image, text, font, image_buffer_id, text_buffer_id):
        # 2px between image and text
        total_w = image.width + \
            self.buffers[text_buffer_id].textsize(text, font=font)[0] + 2
        left = pos[0] + (width - total_w) // 2
        self.draw_image((left, pos[1]), image, image_buffer_id)
        self.draw_text(
            (left + image.width + 2, pos[1]-2), text, font, text_buffer_id)

        if DEBUG_CENTER_BOUNDS:
            self.buffers[text_buffer_id].line(
                [pos, (pos[0], pos[1] + image.height)])
            self.buffers[text_buffer_id].line(
                [(pos[0] + width, pos[1]), (pos[0] + width, pos[1] + image.height)])

    def draw_current_time_other_tz(self, pos, width, font=None, vertical=True):
        if font is None:
            font = self.context.small_font
        dh = font.getsize("Wy")[1]
        if 'secondTZ' in self.config and self.config['secondTZ'] is not None:
            tz = timezone(self.config['secondTZ'])
            now = datetime.datetime.now(tz)
            time = now.strftime(self.context.time_format)
            date = now.strftime(self.context.date_format)
            if vertical:
                self.draw_text_centered(
                    pos, width, now.strftime("- %Z -"), font, self.context.BLACK)
                self.draw_text_centered(
                    (pos[0], pos[1] + dh), width, time, font, self.context.BLACK)
                self.draw_text_centered(
                    (pos[0], pos[1] + dh*2), width, date, font, self.context.BLACK)
            else:
                self.draw_text_centered(
                    pos, width, now.strftime("%Z - " + self.context.time_format), font, self.context.BLACK)
                self.draw_text_centered(
                    (pos[0], pos[1] + dh), width, date, font, self.context.BLACK)

    def draw_sun(self, pos, width):
        observer = Observer(
            latitude=self.config['position']['lat'],
            longitude=self.config['position']['lon'])

        tz = tzlocal()
        s = sun(observer, tzinfo=tz)
        rise_time = s['sunrise'].strftime(self.context.time_format)
        set_time = s['sunset'].strftime(self.context.time_format)

        self.draw_icon_text_centered(pos, width // 2, self.context.sunrise, rise_time,
                                     self.context.tiny_font, self.context.RED, self.context.BLACK)
        self.draw_icon_text_centered((pos[0] + width // 2, pos[1]), width // 2, self.context.sunrise,
                                     set_time, self.context.tiny_font, self.context.RED, self.context.BLACK)

    def draw_current_date(self, pos, width):
        now = datetime.datetime.now()
        date = now.strftime(self.context.date_format)
        if width is None:
            self.draw_text(pos, date, self.context.med_font,
                           self.context.BLACK)
        else:
            self.draw_text_centered(pos, width, date,
                                    self.context.med_font, self.context.BLACK)


class DigitalClockDisplay(BaseDisplay):
    LARGE_CLOCK_BOTTOM = 72
    SECONDARY_START = 95

    def __init__(self, config, context):
        super().__init__(config, context)
        self.config = config
        self.context = context
        self.buffers = []

    def draw_current_time(self):
        now = datetime.datetime.now()
        time = now.strftime(self.context.time_format)
        self.draw_text_centered((0, -10), self.context.width, time,
                                self.context.big_font, self.context.BLACK)

        self.draw_current_date((0, 40), self.context.width)

        # self.buffers[self.context.RED].line([(2, self.SECONDARY_START),
        #                                      (self.context.width-2, self.SECONDARY_START)], fill=0, width=1)

    def draw_time_data(self, buffers):
        self.buffers = buffers
        """Draws time-related information: current time/date, second TZ time/date, sunrise, sunset times"""
        self.draw_current_time()
        self.draw_sun((0, self.LARGE_CLOCK_BOTTOM), self.context.width)
        self.draw_current_time_other_tz(
            (0, self.SECONDARY_START), self.context.width // 2)

    def refresh_time(self):
        return 60


class AnalogClockDisplay(BaseDisplay):
    CLOCK_FACE = 90
    OFFSET = 5

    def __init__(self, config, context):
        super().__init__(config, context)
        self.config = config
        self.context = context
        self.buffers = []

    def draw_analog_time(self, pos, width):
        radius = width / 2
        center = (pos[0] + radius, pos[1] + radius)
        br = (pos[0] + width, pos[1] + width)  # bottom right corner

        now = datetime.datetime.now()
        hr_angle = (now.hour % 12 + now.minute / 60.0) * 30.0 - 90
        min_angle = now.minute * 6 - 90

        hr_x = radius*0.6 * \
            math.cos(math.radians(hr_angle)) + pos[0] + radius
        hr_y = radius*0.6 * \
            math.sin(math.radians(hr_angle)) + pos[1] + radius

        min_x = radius * 0.9 * \
            math.cos(math.radians(min_angle)) + pos[0] + radius
        min_y = radius * 0.9 * \
            math.sin(math.radians(min_angle)) + pos[1] + radius

        # clock face
        self.buffers[self.context.BLACK].ellipse(
            [pos, br], fill=1, outline=0, width=2)
        # hour hand
        self.buffers[self.context.BLACK].line(
            [center, (hr_x, hr_y)], fill=0, width=3)
        # minute hand
        self.buffers[self.context.RED].line(
            [center, (min_x, min_y)], fill=0, width=2)
        # digital time
        self.draw_text_centered((pos[0], pos[1] + width - 25), width, now.strftime(self.context.time_format),
                                self.context.tiny_font, self.context.RED)

    def draw_time_data(self, buffers):
        self.buffers = buffers
        """Draws time-related information: current time/date, second TZ time/date, sunrise, sunset times"""

        clock_bound = self.OFFSET + self.CLOCK_FACE

        self.draw_analog_time((self.OFFSET, self.OFFSET), self.CLOCK_FACE)
        self.draw_current_date(
            (clock_bound, 0), self.context.width - clock_bound)
        self.draw_sun((clock_bound, 30), self.context.width - clock_bound)
        self.draw_current_time_other_tz(
            (clock_bound, 50), self.context.width - clock_bound, font=self.context.tiny_font, vertical=False)

    def refresh_time(self):
        return 120


class Display:
    def __init__(self, config, context):
        self.config = config
        self.context = context
        self.digital = 'mode' in self.config and self.config['mode'] == 'digital'

        self.time_display = DigitalClockDisplay(
            config, context) if self.digital else AnalogClockDisplay(config, context)
        self.weather_display = None

    def update_weather(self, weather):
        if self.weather_display is not None:
            self.weather_display.update_weather(weather)

    def draw_display(self, buffers):
        self.time_display.draw_time_data(buffers)
        if self.weather_display is not None:
            self.weather_display.draw_weather_data(buffers)
        self.draw_frames()

    def draw_digital_frame(self):
        pass

    def draw_analog_frame(self):
        pass

    def draw_frames(self):
        if self.digital:
            self.draw_digital_frame()
        else:
            self.draw_analog_frame()
