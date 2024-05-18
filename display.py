import json
import sys
from pprint import pprint

from adafruit_character_lcd.character_lcd import Character_LCD_Mono
from digitalio import DigitalInOut, Pin

with open('pinout.json') as f:
    pins = json.load(f)['display_bcm_pins']

# vss = GND (https://pinout.xyz/pinout/ground)
# vdd = 5V (https://pinout.xyz/pinout/5v_power)
# v0 = middle of trimpot
rs = DigitalInOut(Pin(pins['RS']))
en = DigitalInOut(Pin(pins['EN']))
d4 = DigitalInOut(Pin(pins['D4']))
d5 = DigitalInOut(Pin(pins['D5']))
d6 = DigitalInOut(Pin(pins['D6']))
d7 = DigitalInOut(Pin(pins['D7']))

columns = 16
rows = 2

lcd = Character_LCD_Mono(rs, en, d4, d5, d6, d7, columns, rows)

backslash = '\x00'
lcd.create_char(0, [0, 0, 16, 8, 4, 2, 1, 0])

left_arrow = '\x01'
lcd.create_char(1, [0, 2, 6, 14, 6, 2, 0, 0])

up_arrow = '\x02'
lcd.create_char(2, [0, 0, 4, 14, 31, 0, 0, 0])

right_arrow = '\x03'
lcd.create_char(3, [0, 8, 12, 14, 12, 8, 0, 0])

down_arrow = '\x04'
lcd.create_char(4, [0, 0, 31, 14, 4, 0, 0, 0])

if __name__ == "__main__":
    pprint(sys.argv)
    lcd.clear()
    lcd.message = sys.argv[-1]
