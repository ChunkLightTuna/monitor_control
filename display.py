#!/usr/bin/python3

import sys
from pprint import pprint

import adafruit_character_lcd.character_lcd as characterlcd
import board
import digitalio

rs = digitalio.DigitalInOut(board.D21)
en = digitalio.DigitalInOut(board.D16)
d4 = digitalio.DigitalInOut(board.D19)
d5 = digitalio.DigitalInOut(board.D22)
d6 = digitalio.DigitalInOut(board.D24)
d7 = digitalio.DigitalInOut(board.D14)

columns = 16
rows = 2

lcd = characterlcd.Character_LCD_Mono(rs, en, d4, d5, d6, d7, columns, rows)

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
    argv = sys.argv

    pprint(argv)
    lcd.clear()
    lcd.message = sys.argv[-1]
