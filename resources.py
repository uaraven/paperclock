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

from PIL import ImageFont, Image


class Resources:
    def __init__(self):
        self.big_font = ImageFont.FreeTypeFont(
            font='data/OpenSans-Bold.ttf', size=50)
        self.med_font = ImageFont.FreeTypeFont(
            font='data/OpenSans-SemiBold.ttf', size=20)
        self.small_font = ImageFont.FreeTypeFont(
            font='data/OpenSans-SemiBold.ttf', size=18)
        self.tiny_font = ImageFont.FreeTypeFont(
            font='data/OpenSans-SemiBold.ttf', size=14)

        self.larger_font = ImageFont.FreeTypeFont(
            font='data/OpenSans-Bold.ttf', size=25)

        # Icons
        self.sunrise = Image.open(
            'data/sunrise.png').convert(mode='1', dither=None)
        self.sunset = Image.open(
            'data/sunset.png').convert(mode='1', dither=None)

        self.icons = {}

    def icon(self, name: str) -> Image:
        if name not in self.icons:
            self.icons[name] = Image.open(f'data/{name}.png').convert(mode='1')
        return self.icons[name]
