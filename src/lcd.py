import json
import sys
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable, Sequence
from typing import Optional

from adafruit_character_lcd.character_lcd import Character_LCD_Mono
from digitalio import DigitalInOut, Pin

from patterns import BACKSLASH, UP_ARROW, DOWN_ARROW, AM, PM, patterns
from patterns import Pattern


def time_str(dt: datetime) -> str:
    return f"{dt.strftime('%I:%M').lstrip('0')}{AM if dt.strftime('%p') == 'AM' else PM}"


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

        if len(line_one) > 16:
            line_one = line_one[:16]
        if len(line_two) > 16:
            line_two = line_two[:16]

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
        self.line_one = f'{f"{self.line_one:<16}"[:14]}2{UP_ARROW}'
        self.line_two = f'{f"{self.line_two:<16}"[:14]}8{DOWN_ARROW}'
        return self

    def __repr__(self):
        return f'{self.line_one}\n{self.line_two}'


class PatternCache:
    def __init__(self, create_char: Callable[[int, Sequence[int]], None]):
        self._create_char = create_char
        self._cache = OrderedDict[int, int]({i: i for i in range(8)})
        assert all(i in [p.i for p in patterns] for i in self._cache)
        for p in patterns:
            if p.i in self._cache:
                self._create_char(p.i, p.seq)

    def __getitem__(self, p: Pattern) -> str:
        if p.i in self._cache:
            self._cache.move_to_end(p.i)
            i = self._cache[p.i]
        else:
            i = self._cache.popitem(last=False)[1]
            self._cache[p.i] = i
            self._create_char(i, p.seq)
        return int.to_bytes(i).decode()


class LCD(Character_LCD_Mono):

    def __init__(self):
        with open('../pinout.json') as f:
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

        self.pattern_cache = PatternCache(self.create_char)
        self.clear()

    def msg(self, m: Msg):
        self.clear()

        s = (
            f'{m.line_one}\n{m.line_two}'
            .replace('\\', str(BACKSLASH))
            .replace('\t', ' ')
        )
        count = 0
        for p in patterns:
            if p.char in s:
                count += 1
                if count > 8:
                    raise Exception('Max 8 symbols per msg')
                s.replace(p.char, self.pattern_cache[p])

        self.message = s


if __name__ == "__main__":
    lcd = LCD()
    lcd.msg(Msg(*sys.argv[1:3]))
