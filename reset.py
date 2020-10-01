import waveshare_epd.epd2in7b as epd

display = epd.EPD()
display.init()
display.Clear()
display.Dev_exit()