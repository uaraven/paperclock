# paperclock
Raspberry Pi driven clock with E-paper screen

## What is it

Clock and weather display using Waveshare e-ink screens, running on Raspberry Pi.

I am using Pi Zero W and [2.7" 3-color Pi HAT e-ink display](https://www.waveshare.com/wiki/2.7inch_e-Paper_HAT_(B)), but this project can be modified to run with any screen.

This project also includes 3d models of enclosure to print.

## Setting up build:

Install dependencies

```sh
apt install python3-rpi.gpio python3-dev gpiozero python3-pip
pip3 install -r requirements.txt
```

Alternatively, instead of using 
[epd-library](https://pypi.org/project/epd-library/) for Waveshare displays, one can install waveshare code manually from their github repo:

```sh
 git clone https://github.com/waveshare/e-Paper.git
 cd e-Paper/RaspberryPi&JetsonNano/python
 python3 setup.py install
```

## Connecting display

Display will be connected to raspberry pi using wires, not 40-pin connector, we'll need
40-pin on the Pi to be free to connect other stuff.

Follow this mapping:
|e-Ink   | Raspberry Pi   |
|:-------|:---------------|
|3.3V    | 3.3V   (pin1)  |
|GND     | GND    (pin6)  |
|DIN     | MOSI   (pin19) |
|CLK     | SCLK   (pin23) |
|CS      | CE0    (pin24) |
|DC      | GPIO25 (pin22) |
|RST     | GPIO17 (pin11) |
|BUSY    | GPIO24 (pin18) |

## Configuring to run

Copy `config-example.json` to either
 - home directory and rename it to `.paperclock`
 - directory containing the application and rename it `config.json`

Set the location. It can be either city name from [supported list](https://astral.readthedocs.io/en/latest/index.html?highlight=city#cities) or a latitude and longitude.

```json
{ 
    "location": "Tripoli"
}
```
OR
```json
{
    "location": {"lat": 0.0, "lon": 0.0}
}
```
Set the second timezone to display. Set it to `null` if you don't want second timezone.

For the weather forecast to work, you'll need to provide API Key for openweathermap. Register at https://home.openweathermap.org/, go to `API`->`One Call API` and click subscribe, follow prompts to create a free API key. Copy the key to "openweathermap_api_key" configuration field.

Configure temperature units you want to use, either `metric` or `imperial` are supported. 
Set whether you want to use 24 or 12 hour clock, use `24h` or `12h` respectively.

Your config file should look like

```json
{
    "location": "Toronto",
    "secondTZ": "Europe/Athens",
    "openweathermap_api_key": "fake012433dkey2342323",
    "units": "metric",
    "time": "24h"
}
```

