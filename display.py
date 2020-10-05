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

import math
import datetime
from pytz import timezone
from dateutil.tz import tzlocal
from threading import Timer

from astral import Observer
from PIL import Image, ImageDraw
from astral.sun import sun

from settings import Settings
from resources import Resources
from openweathermap import WeatherInfo, wind_direction_to_compass

import waveshare_epd.epd2in7b as epd


DEBUG_CENTER_BOUNDS = False


class Display:
    """Manages e-ink display, its buffers and provides methods for drawing"""
    BLACK = 0
    RED = 1

    def __init__(self, settings: Settings):
        self.settings = settings
        self.eInk = epd.EPD()

        self.settings = settings
        self.digital = self.settings.mode == 'digital'

        # horizontal display, so switch width and height
        self.screen_size = (self.eInk.height, self.eInk.width)

        self.last_refresh_start = datetime.datetime.fromtimestamp(0)
        self.buffers = []

    def width(self):
        return self.screen_size[0]

    def height(self):
        return self.screen_size[1]

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

    def draw_image_centered(self, xy, width, image, buffer_id=0):
        dx = xy[0] + (width - image.width)//2
        self.buffers[buffer_id + 2].paste(image, (dx, xy[1]))

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

    def line(self, xy1, xy2, color, fill=0, width=1):
        self.buffers[color].line([xy1, xy2], fill=fill, width=width)

    def rect(self, tl, br, color, fill=0, outline=0):
        self.buffers[color].rectangle([tl, br], fill, outline)

    def ellipse(self, tl, br, color, fill=0, outline=0, width=1):
        self.buffers[color].ellipse([tl, br], fill, outline, width)

    def new_screen(self):
        """Initialize buffers for the new frame"""
        blackimage = Image.new('1', self.screen_size, 255)
        redimage = Image.new('1', self.screen_size, 255)
        drawblack = ImageDraw.Draw(blackimage)
        drawred = ImageDraw.Draw(redimage)

        self.buffers = (drawblack, drawred, blackimage, redimage)
        return self.buffers

    def show(self):
        """Draw the screen and show it on the e-ink display"""
        now = datetime.datetime.now()
        if (now - self.last_refresh_start) > datetime.timedelta(seconds=25):
            self.last_refresh_start = now
            self.eInk.init()
            self.eInk.display(self.eInk.getbuffer(
                self.buffers[2]), self.eInk.getbuffer(self.buffers[3]))
            self.eInk.sleep()
            return True
        else:
            print("display is refreshing, ignoring refresh")
            return False


class Weather:
    DEFAULT = 0
    CURRENT_DETAILS = 1

    def __init__(self, display: Display, resources: Resources):
        self.display = display
        self.weather_info = None
        self.res = resources
        self.state = self.DEFAULT
        self.state_timer = None

    def update(self, weather_info: WeatherInfo):
        self.weather_info = weather_info

    def set_state(self, new_state):
        print(f'state change, current: {self.state}, new: {new_state}')
        if self.state == new_state:
            return
        if self.state_timer is not None:
            self.state_timer.cancel()
            self.state_time = None
        self.state = new_state
        if self.state != self.DEFAULT:
            print('setting timer to 25 seconds')
            self.state_timer = Timer(
                25, lambda: self.set_state(self.DEFAULT)).start()

    def draw_hourly_pop(self, pos, width, height):
        if self.weather_info is None:
            return
        hourly_pop = [
            m.pop*100 for m in self.weather_info.hourly][0:8]
        scale_y = height / 100.0  # max pop is always 100%
        scale_x = math.trunc(width / len(hourly_pop))

        bottom = pos[1] + height
        x = 0
        for m in hourly_pop:
            self.display.rect((pos[0] + x, int(bottom - m*scale_y)), (pos[0] +
                                                                      x + scale_x - 5, bottom), self.display.BLACK, fill=0, outline=0)
            x += scale_x
        self.display.line((pos[0], pos[1]), (x, pos[1]), self.display.RED)

    def draw_wind(self, pos, width):
        if self.weather_info is None:
            return
        current = self.weather_info.current
        speed = round(current.wind_speed * 3.6, 1)  # m/s -> km/h
        wind = self.res.icon('weather/wind')
        wind = wind.rotate(current.wind_direction, fillcolor=1)

        icon_offset_x = (width - wind.width) // 2

        self.display.draw_image(
            (pos[0] + icon_offset_x, pos[1]), wind, self.display.RED)
        self.display.draw_text_centered((pos[0], pos[1] + 30), width, wind_direction_to_compass(
            current.wind_direction), self.res.tiny_font, self.display.BLACK)
        self.display.draw_text_centered(
            (pos[0], pos[1] + 50), width, str(speed), self.res.tiny_font, self.display.BLACK)

    def draw_current_weather(self):
        pos = (5, 99)
        if self.weather_info is not None:
            icon = self.res.icon(
                f'weather/{self.weather_info.current.weather[0].icon}')
            self.display.draw_image(pos, icon, self.display.RED)
            # current weather
            self.display.draw_text((pos[0] + 70, pos[1] + 22),
                                   self.weather_info.current.weather[0].description, self.res.tiny_font, self.display.BLACK)
            # current temperature
            self.display.draw_text((pos[0] + 70, pos[1] - 5),
                                   f'{self.weather_info.current.temperature} º',
                                   self.res.larger_font, self.display.BLACK)

            # precipitation minutely - 15 pixels for graph
            self.draw_hourly_pop(
                (0, self.display.screen_size[1] - 15), self.display.screen_size[0] - 65, 15)

            # wind
            self.draw_wind((self.display.screen_size[0] - 65, pos[1]), 65)

    def draw_weather_data(self):
        if self.state == self.DEFAULT:
            self.draw_current_weather()
        else:
            self.draw_current_details()

    def draw_current_details(self):
        if self.weather_info is not None:
            icon = self.res.icon(
                f'weather/{self.weather_info.current.weather[0].icon}')
            self.display.draw_image_centered(
                (0, 0), self.display.width() // 2, icon,  self.display.RED)
            # current weather
            self.display.draw_text((3, 50),
                                   self.weather_info.current.weather[0].description, self.res.med_font, self.display.BLACK)
            # current temperature

            self.display.draw_text((self.display.screen_size[0] // 2, 0),
                                   f'{self.weather_info.current.temperature}º',
                                   self.res.larger_font, self.display.BLACK)

            self.display.draw_text((self.display.screen_size[0] // 2, 25),
                                   f'{self.weather_info.current.feels_like}º',
                                   self.res.larger_font, self.display.RED)

            self.display.draw_text((3, 80),
                                   f'Humidity: {self.weather_info.current.humidity}%', self.res.med_font, self.display.BLACK)
            self.display.draw_text((3, 100), f'Pressure: {self.weather_info.current.pressure}hPa',
                                   self.res.med_font, self.display.BLACK)
            self.display.draw_text((3, 120), f'UV Index: {self.weather_info.current.uvi}',
                                   self.res.med_font, self.display.BLACK)


class Clock:
    CLOCK_FACE = 90
    OFFSET = 5

    def __init__(self, display: Display, resources: Resources, settings: Settings) -> None:
        self.display = display
        self.settings = settings
        self.res = resources

    def draw_current_time_other_tz(self, pos, width, font=None, vertical=True):
        if font is None:
            font = self.res.small_font
        dh = font.getsize("Wy")[1]
        if self.settings.secondTZ is not None:
            tz = timezone(self.settings.secondTZ)
            now = datetime.datetime.now(tz)
            time = now.strftime(self.settings.time_format)
            date = now.strftime(self.settings.date_format)
            black = self.display.BLACK
            if vertical:
                self.display.draw_text_centered(
                    pos, width, now.strftime("- %Z -"), font, black)
                self.display.draw_text_centered(
                    (pos[0], pos[1] + dh), width, time, font, black)
                self.display.draw_text_centered(
                    (pos[0], pos[1] + dh*2), width, date, font, black)
            else:
                self.display.draw_text_centered(pos, width, now.strftime(
                    "%Z - " + self.settings.time_format), font, black)
                self.display.draw_text_centered(
                    (pos[0], pos[1] + dh), width, date, font, black)

    def draw_sun(self, pos, width):
        observer = Observer(
            latitude=self.settings.position['lat'],
            longitude=self.settings.position['lon'])

        tz = tzlocal()
        s = sun(observer, tzinfo=tz)
        rise_time = s['sunrise'].strftime(self.settings.time_format)
        set_time = s['sunset'].strftime(self.settings.time_format)

        self.display.draw_icon_text_centered(pos, width // 2, self.res.sunrise, rise_time,
                                             self.res.tiny_font, self.display.RED, self.display.BLACK)
        self.display.draw_icon_text_centered((pos[0] + width // 2, pos[1]), width // 2, self.res.sunrise,
                                             set_time, self.res.tiny_font, self.display.RED, self.display.BLACK)

    def draw_current_date(self, pos, width):
        now = datetime.datetime.now()
        date = now.strftime(self.settings.date_format)
        if width is None:
            self.display.draw_text(pos, date, self.res.med_font,
                                   self.display.BLACK)
        else:
            self.display.draw_text_centered(pos, width, date,
                                            self.res.med_font, self.display.BLACK)

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
        self.display.ellipse(pos, br, self.display.BLACK,
                             fill=1, outline=0, width=2)
        # hour hand
        self.display.line(center, (hr_x, hr_y),
                          self.display.BLACK, fill=0, width=3)
        # minute hand
        self.display.line(center, (min_x, min_y),
                          self.display.BLACK, fill=0, width=2)
        # digital time
        self.display.draw_text_centered((pos[0], pos[1] + width - 25), width, now.strftime(self.settings.time_format),
                                        self.res.tiny_font, self.display.RED)

    def draw_time_data(self):
        """Draws time-related information: current time/date, second TZ time/date, sunrise, sunset times"""

        clock_bound = self.OFFSET + self.CLOCK_FACE

        self.draw_analog_time(
            (self.OFFSET, self.OFFSET), self.CLOCK_FACE)
        self.draw_current_date(
            (clock_bound, 0), self.display.width() - clock_bound)
        self.draw_sun((clock_bound, 30), self.display.width() - clock_bound)
        self.draw_current_time_other_tz(
            (clock_bound, 50), self.display.width() - clock_bound, font=self.res.tiny_font, vertical=False)


class Layout:
    """Layout knows how to draw stuff. It draws common stuff itself or delegates specialized drawing to subclasses
       Layout is also responsible for drawing borders
    """

    def __init__(self, display: Display, settings: Settings) -> None:
        self.display = display
        self.settings = settings
        self.resources = Resources()
        self.weather = Weather(display, self.resources)
        self.clock = Clock(self.display, self.resources, settings)

    def draw(self):
        self.display.new_screen()
        self._draw_frame()
        if (self.weather.state == self.weather.DEFAULT):
            self.clock.draw_time_data()
        self.weather.draw_weather_data()
        self.display.show()

    def _draw_frame(self):
        if (self.weather.state == self.weather.DEFAULT):
            self.display.line(
                (10, 97), (self.display.screen_size[0] - 10, 97), self.display.BLACK)
