import json
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from adafruit_character_lcd.character_lcd import Character_LCD_Mono
from digitalio import DigitalInOut, Pin

BACKSLASH = '\x00'
LEFT_ARROW = '\x01'
UP_ARROW = '\x02'
RIGHT_ARROW = '\x03'
DOWN_ARROW = '\x04'
FAHRENHEIT = '\x05'
MOON = '\x06'
SUN = '\x07'


class Align(Enum):
    NONE = 0
    LEFT = 1
    RIGHT = 2
    CENTER = 3


@dataclass
class Msg:
    line_one: str
    line_two: str

    def __init__(
            self,
            line_one: str,
            line_two: Optional[str] = None,
            align_one: Align = Align.NONE,
            align_two: Align = Align.NONE
    ):
        if not line_two:
            if '\n' in line_one:
                line_one, line_two = line_one.split('\n')[:2]
            else:
                line_two = ''

        match align_one:
            case Align.LEFT:
                line_one = line_one.lstrip()
            case Align.RIGHT:
                line_one = line_one.rjust(16)
            case Align.CENTER:
                line_one = line_one.center(16, ' ')

        match align_two:
            case Align.LEFT:
                line_two = line_two.lstrip()
            case Align.RIGHT:
                line_two = line_two.rjust(16)
            case Align.CENTER:
                line_two = line_two.center(16, ' ')

        self.line_one = line_one
        self.line_two = line_two

    def add_arrows(self):
        self.line_one = f"{self.line_one:<16}"[:14] + '2' + UP_ARROW
        self.line_two = f"{self.line_two:<16}"[:14] + '8' + DOWN_ARROW
        return self

    def __repr__(self):
        return f'{self.line_one}\n{self.line_two}'


class LCD(Character_LCD_Mono):

    def __init__(self):
        with open('pinout.json') as f:
            pins = json.load(f)['display_bcm_pins']

        # vss = GND (https://pinout.xyz/pinout/ground)
        # vdd = 5V (https://pinout.xyz/pinout/5v_power)
        # v0 = middle of trimpot
        super().__init__(
            rs=DigitalInOut(Pin(pins['RS'])),
            en=DigitalInOut(Pin(pins['EN'])),
            db4=DigitalInOut(Pin(pins['D4'])),
            db5=DigitalInOut(Pin(pins['D5'])),
            db6=DigitalInOut(Pin(pins['D6'])),
            db7=DigitalInOut(Pin(pins['D7'])),
            columns=16,
            lines=2
        )

        self.create_char(0, [0, 0, 16, 8, 4, 2, 1, 0])  # backslash
        self.create_char(1, [0, 2, 6, 14, 6, 2, 0, 0])  # arrow left
        self.create_char(2, [0, 0, 4, 14, 31, 0, 0, 0])  # arrow up
        self.create_char(3, [0, 8, 12, 14, 12, 8, 0, 0])  # arrow right
        self.create_char(4, [0, 0, 31, 14, 4, 0, 0, 0])  # arrow down
        self.create_char(5, [24, 24, 7, 4, 7, 4, 4, 0])  # fahrenheit
        self.create_char(6, [0, 14, 31, 31, 31, 14, 0, 0])  # moon
        self.create_char(7, [0, 14, 17, 17, 17, 14, 0, 0])  # sun
        self.clear()

    def msg(self, m: Msg):
        self.clear()
        self.message = f'{m.line_one}\n{m.line_two}'.replace('\\', BACKSLASH)


if __name__ == "__main__":
    lcd = LCD()
    lcd.msg(Msg(*sys.argv[1:3]))
