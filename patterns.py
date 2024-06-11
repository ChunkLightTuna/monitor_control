import gc
from typing import Sequence


class Pattern(object):
    _i = 0

    def __init__(self, *seq: int):
        assert (len(seq) == 8)
        self.i = Pattern._i
        Pattern._i += 1
        self.char = int.to_bytes(self.i).decode()
        self.seq = seq

    def __repr__(self):
        return self.char

    def __str__(self):
        return self.char

    def __format__(self, format_spec):
        return self.char


BACKSLASH = Pattern(0, 0, 16, 8, 4, 2, 1, 0)
UP_ARROW = Pattern(0, 0, 4, 14, 31, 0, 0, 0)
DOWN_ARROW = Pattern(0, 0, 31, 14, 4, 0, 0, 0)
AM = Pattern(4, 10, 14, 10, 0, 10, 21, 17)
PM = Pattern(12, 10, 12, 8, 0, 10, 21, 17)
FAHRENHEIT = Pattern(24, 24, 7, 4, 7, 4, 4, 0)
MOON = Pattern(0, 14, 31, 31, 31, 14, 0, 0)
SUN = Pattern(0, 14, 17, 17, 17, 14, 0, 0)
LEFT_ARROW = Pattern(0, 2, 6, 14, 6, 2, 0, 0)
RIGHT_ARROW = Pattern(0, 8, 12, 14, 12, 8, 0, 0)

patterns: Sequence[Pattern] = [o for o in gc.get_objects() if isinstance(o, Pattern)]
