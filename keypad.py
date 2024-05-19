import asyncio
import json
import logging
from dataclasses import dataclass

from adafruit_debouncer import Debouncer
from digitalio import DigitalInOut, Pin

interval = 1 / 700


@dataclass
class SyntheticButton:
    label: str
    press: callable
    value: bool = False

    def __init__(self, label: str):
        self.label = label
        self.press = lambda: logging.info(f"{label} pressed")


class Keypad:
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
        for pin in self.cols:
            pin.switch_to_output()
        self.rows = [
            Debouncer(DigitalInOut(Pin(pin)), interval=interval)
            for pin in pins['rows']
        ]

        self._buttons = [
            [SyntheticButton(self.labels[ri][ci]) for ci, _ in enumerate(self.cols)]
            for ri, _ in enumerate(self.rows)
        ]

    @property
    def buttons(self):
        return dict([(button.label, button) for row in self._buttons for button in row])

    def run(self):
        event_loop = asyncio.get_event_loop()

        async def f():

            r = range(4)
            while True:
                for row in range(4):
                    for col in r:
                        self.cols[col].value = True
                        await asyncio.sleep(interval)
                        self.rows[row].update()
                        new = self.rows[row].value
                        self.cols[col].value = False
                        button = self._buttons[row][col]
                        if button.value ^ new:
                            button.value = new
                            if new:
                                button.press()

        event_loop.create_task(f())
        event_loop.run_forever()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    Keypad().run()
