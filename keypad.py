#!/usr/bin/python3
import logging
from signal import pause

from gpiozero import DigitalInputDevice, DigitalOutputDevice
from gpiozero.threads import GPIOThread


class SyntheticButton():
    def __init__(self, label):
        self._value = 0
        self.label = label
        self._when_pressed = lambda: logging.info(f"{label} pressed")

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    @property
    def when_pressed(self):
        return self._when_pressed

    @when_pressed.setter
    def when_pressed(self, fun):
        self._when_pressed = fun


class Pad:

    def __init__(self):
        col_pins = [2, 3, 4, 5],
        row_pins = [6, 7, 8, 9],
        labels = [
            ['1', '2', '3', 'A'],
            ['4', '5', '6', 'B'],
            ['7', '8', '9', 'C'],
            ['*', '0', '#', 'D']
        ]

        self._cols = [DigitalOutputDevice(pin) for pin in col_pins]
        self._rows = [DigitalInputDevice(pin) for pin in row_pins]

        self._labels = labels

        self._buttons = [[SyntheticButton(self._labels[row][col]) for col in range(len(self._cols))] for row in
                         range(len(self._rows))]

        self._event_thread = None
        self._event_delay = .02  # 50hz takes 40% cpu!

        self._col_range = range(len(self._cols))
        self._row_range = range(len(self._rows))

    @property
    def buttons(self):
        return dict([(button.label, button) for row in self._buttons for button in row])

    def _scan(self):
        for row in self._row_range:
            for col in self._col_range:
                self._cols[col].value = 1
                new = self._rows[row].value
                self._cols[col].value = 0

                button = self._buttons[row][col]
                if button.value ^ new:
                    button.value = new
                    # should be in another thread?
                    if new:
                        button.when_pressed()

    def _event_loop(self):
        while not self._event_thread.stopping.wait(self._event_delay):
            self._scan()

    def start(self):
        self._event_thread = GPIOThread(target=self._event_loop)
        self._event_thread.start()

    def stop(self):
        self._event_thread.stop()
        self._event_thread = None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    pad = Pad()
    pad.start()

    pause()
