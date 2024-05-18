import json
import logging
import signal
from dataclasses import dataclass
from threading import Thread

from adafruit_blinka.microcontroller.bcm283x.pin import Pin
from digitalio import DigitalInOut


@dataclass
class SyntheticButton:
    label: str
    when_pressed: callable
    value: bool = False

    def __init__(self, label: str):
        self.label = label
        self.when_pressed = lambda: logging.info(f"{label} pressed")


class Pad:
    labels = [
        ['1', '2', '3', 'A'],
        ['4', '5', '6', 'B'],
        ['7', '8', '9', 'C'],
        ['*', '0', '#', 'D']
    ]

    def __init__(self):
        with open('pinout.json') as f:
            pins = json.load(f)['keypad_bcm_pins']

        self.cols = [DigitalInOut(Pin(pin)) for pin in pins['cols']]
        self.rows = [DigitalInOut(Pin(pin)) for pin in pins['rows']]
        for pin in self.cols:
            pin.switch_to_output()

        self._buttons = [
            [SyntheticButton(self.labels[ri][ci]) for ci, _ in enumerate(self.cols)]
            for ri, _ in enumerate(self.rows)
        ]

        self._event_thread = None
        self._event_delay = .02  # 50hz takes 40% cpu!

    @property
    def buttons(self):
        return dict([(button.label, button) for row in self._buttons for button in row])

    def _scan(self):
        for row_i, row in enumerate(self.rows):
            for col_i, col in enumerate(self.cols):
                col.value = True
                new = row.value
                col.value = False

                button = self._buttons[row_i][col_i]
                if button.value ^ new:
                    button.value = new
                    # should be in another thread?
                    if new:
                        button.when_pressed()

    def _event_loop(self):
        while not self._event_thread.stopping.wait(self._event_delay):
            self._scan()

    def start(self):
        self._event_thread = Thread(target=self._event_loop)
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

    signal.pause()
