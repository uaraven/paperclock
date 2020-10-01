#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import waveshare_epd.epd2in7b as epd
import time
import datetime
from pytz import timezone
from dateutil.tz import tzlocal
from PIL import Image, ImageDraw, ImageFont
from gpiozero import Button
import json
import asyncio
import sys
import os
from astral import Observer
from astral.geocoder import lookup, database
from astral.sun import sun
import threading

display = epd.EPD()

# horizontal display
width = display.height
height = display.width

big_font = ImageFont.FreeTypeFont(font='data/OpenSans-Bold.ttf', size=50)
med_font = ImageFont.FreeTypeFont(font='data/OpenSans-SemiBold.ttf', size=20)
small_font = ImageFont.FreeTypeFont(font='data/OpenSans-SemiBold.ttf', size=18)
sunrise = Image.open('data/sunrise.png').convert(mode='1', dither=None)
sunset = Image.open('data/sunset.png').convert(mode='1', dither=None)

def make_buffers():
  blackimage = Image.new('1', (display.height, display.width), 255)  # 255: clear the frame
  redimage = Image.new('1', (display.height, display.width), 255)  # 255: clear the frame
  drawblack = ImageDraw.Draw(blackimage)
  drawred = ImageDraw.Draw(redimage)
  
  return (drawblack, drawred, blackimage, redimage)
  
def show(buffers):
  display.init()
  display.display(display.getbuffer(buffers[2]), display.getbuffer(buffers[3]))
  display.sleep()

def draw_text(xy, text, font, buffers, buffer_id):
  buffers[buffer_id].text(xy, text, font=font, fill=0)

def draw_current_time(buffers):
  now = datetime.datetime.now()
  time = now.strftime("%H:%M")
  tsize = buffers[0].textsize(time, font = big_font)
  x = (width - tsize[0]) / 2
  buffers[0].text((x, -10), time, font=big_font, fill=0)
  date = now.strftime("%b %d, %Y")
  dsize = buffers[0].textsize(date, font = med_font)
  x = (width - tsize[0]) / 2
  buffers[0].text((x + 12, tsize[1] - 10), date, font=med_font, fill=0)

def draw_current_time_other_tz(buffers, tz):
  now = datetime.datetime.now(tz)
  time = now.strftime("%H:%M %Z")
  buffers[0].text((5, 75), time, font=small_font, fill=0)
  date = now.strftime("%b %d, %Y")
  buffers[0].text((5, 95), date, font=small_font, fill=0)

def draw_sun(buffers, config):
  if isinstance(config['location'], str):
    location = lookup(config['location'], database())
    observer = location.observer
  else:
    observer = Observer(
      latitude=config['location']['lat'],
      longitude=config['location']['lon'])

  tz = tzlocal()
  s = sun(observer, tzinfo=tz)
  rise_time = s['sunrise'].strftime("%H:%m")
  set_time = s['sunset'].strftime("%H:%m")

  draw_image((5, 125), sunrise, buffers, 1)
  draw_text((25, 118), rise_time, small_font, buffers, 0)
  draw_image((5, 145), sunset, buffers, 1)  
  draw_text((25, 138), set_time, small_font, buffers, 0)

def draw_image(xy, image, buffers, buffer_id=0):
  buffers[buffer_id + 2].paste(image, xy)

def draw_time_data(buffers, config):
  """Draws time-related information: current time/date, second TZ time/date, sunrise, sunset times"""
  draw_current_time(buffers)
  draw_current_time_other_tz(buffers, timezone(config['secondTZ']))
  draw_sun(buffers, config)

def redraw_display(config):
  """Draws display"""
  buffers = make_buffers()
  draw_time_data(buffers, config)
  buffers[0].line([(width/2-2, 75),(width/2-2, height)], fill=1, width=5)

  show(buffers)


def timed_execution(config):
  while True:
    redraw_display(config)
    s_left = 60 - datetime.datetime.now().second
    time.sleep(s_left)

  
def load_config():
  if os.path.isfile('config.json'):
    name = 'config.json'
  else:
    name = os.path.join(sys.getenv('$USER'), '.paperclock')
  with open(name) as config:
    return json.load(config)

default_config = {
  "location": {
    'lat': 0.0,
    'lon': 0.0
  },
  "secondTZ": "UTC"
}

if __name__ == '__main__':
  try:
    config = load_config()
  except:
    print('Using default config')
    config = default_config

  # init_display()
  redraw_display(config)

  clock_thread = threading.Thread(target=lambda: timed_execution(config))
  # wait till next minute
  s_left = 60 - datetime.datetime.now().second
  time.sleep(s_left)
  clock_thread.start()


