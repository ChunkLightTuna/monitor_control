import json
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from adafruit_character_lcd.character_lcd import Character_LCD_Mono
from digitalio import DigitalInOut, Pin

backslash = '\x00'
left_arrow = '\x01'
up_arrow = '\x02'
right_arrow = '\x03'
down_arrow = '\x04'


class Align(Enum):
    NONE = 0
    LEFT = 1
    RIGHT = 2
    CENTER = 3


@dataclass
class Message:
    line_one: str
    line_two: str

    def __init__(self, line_one: str, line_two: Optional[str] = None):
        if not line_two:
            if '\n' in line_one:
                line_one, line_two = line_one.split('\n')
            else:
                line_two = ''

        self.line_one = line_one
        self.line_two = line_two

    def add_arrows(self):
        self.line_one = f"{self.line_one:<16}"[:14] + '2' + up_arrow
        self.line_two = f"{self.line_two:<16}"[:14] + '8' + down_arrow
        return self


class Messageable:
    def msg(self, message: Message, align: Align = Align.NONE):
        pass


class LCD(Character_LCD_Mono, Messageable):

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
            lines=16,
            rows=2
        )

        self.create_char(0, [0, 0, 16, 8, 4, 2, 1, 0])  # backslash
        self.create_char(1, [0, 2, 6, 14, 6, 2, 0, 0])  # arrow left
        self.create_char(2, [0, 0, 4, 14, 31, 0, 0, 0])  # arrow up
        self.create_char(3, [0, 8, 12, 14, 12, 8, 0, 0])  # arrow right
        self.create_char(4, [0, 0, 31, 14, 4, 0, 0, 0])  # arrow down
        self.clear()

    def msg(self, m: Message | str, align: Align = Align.NONE):
        if isinstance(m, str):
            m = Message(m)

        match align:
            case Align.LEFT:
                m.line_one = m.line_one.lstrip()
                m.line_two = m.line_two.lstrip()
            case Align.RIGHT:
                m.line_one = f"{m.line_one:>16}"
                m.line_two = f"{m.line_two:>16}"
            case Align.CENTER:
                m.line_one = m.line_one.center(16, ' ')
                m.line_two = m.line_two.center(16, ' ')

        self.clear()
        self.message = f'{m.line_one}\n{m.line_two}'.replace('\\', backslash)


if __name__ == "__main__":
    lcd = LCD()
    lcd.msg(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
