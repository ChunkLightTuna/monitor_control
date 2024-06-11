import gc
from typing import Sequence


class Pattern:
    def __init__(self, char: str, seq: Sequence[int]):
        self.char = char
        self.seq = seq

    def __repr__(self):
        return self.char

    def __str__(self):
        return self.char

    def __format__(self, format_spec):
        return self.char


BACKSLASH = Pattern('\x00', [0, 0, 16, 8, 4, 2, 1, 0])
UP_ARROW = Pattern('\x01', [0, 2, 6, 14, 6, 2, 0, 0])
DOWN_ARROW = Pattern('\x02', [0, 0, 4, 14, 31, 0, 0, 0])
AM = Pattern('\x03', [0, 8, 12, 14, 12, 8, 0, 0])
PM = Pattern('\x04', [0, 0, 31, 14, 4, 0, 0, 0])
FAHRENHEIT = Pattern('\x05', [24, 24, 7, 4, 7, 4, 4, 0])
MOON = Pattern('\x06', [0, 14, 31, 31, 31, 14, 0, 0])
SUN = Pattern('\x07', [0, 14, 17, 17, 17, 14, 0, 0])
LEFT_ARROW = Pattern('\x08', [0, 2, 6, 14, 6, 2, 0, 0])
RIGHT_ARROW = Pattern('\x09', [0, 8, 12, 14, 12, 8, 0, 0])

patterns: Sequence[Pattern] = [o for o in gc.get_objects() if isinstance(o, Pattern)]

assert len(patterns) == len(set(p.char for p in patterns)), "Non-unique char"
