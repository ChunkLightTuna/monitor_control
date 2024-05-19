import asyncio
import json
import logging
from dataclasses import dataclass

from adafruit_debouncer import Debouncer
from digitalio import DigitalInOut, Pin


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
            Debouncer(DigitalInOut(Pin(pin)))
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
            wait = 1 / 8
            cols = enumerate(self.cols)
            rows = enumerate(self.rows)
            while True:
                for col_i, col in cols:
                    col.value = True
                    await asyncio.sleep(wait)
                    for row_i, row in rows:
                        row.update()
                        new = row.value
                        button = self._buttons[row_i][col_i]
                        print(f'{button.label=} {button.value=} {new=}')
                        if button.value ^ new:

                            button.value = new
                            if new:
                                button.press()
                    col.value = False

        event_loop.create_task(f())
        event_loop.run_forever()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    Keypad().run()
