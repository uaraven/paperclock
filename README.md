# paperclock
Raspberry Pi driven clock with E-paper screen

## What is it

Clock and weather display using Waveshare e-ink screens, running on Raspberry Pi.

I am using Pi Zero W and 2.7 inch 3 color Pi HAT e-ink display, but this project can be modified to run with any screen.

This project also includes 3d models of enclosure to print.

## Setting up build:

Install dependencies

```sh
apt install python3-rpi.gpio python-dev gpiozero python3-pip
pip3 install -r requirements.txt
```

Alternatively, instead of using 
[epd-library](https://pypi.org/project/epd-library/) for Waveshare displays, one can install waveshare code manually from their github repo:

```sh
 git clone https://github.com/waveshare/e-Paper.git
 cd e-Paper/RaspberryPi&JetsonNano/python
 python3 setup.py install
```
