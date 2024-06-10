import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Callable

from digitalio import Pin
from keypad import KeyMatrix

BUTTON_LABELS = [
    '1', '2', '3', 'A',
    '4', '5', '6', 'B',
    '7', '8', '9', 'C',
    '*', '0', '#', 'D'
]


@dataclass
class SyntheticButton:
    label: str
    press: Callable[[], None]
    value: bool = False

    def __init__(self, label: str):
        self.label = label
        self.press = lambda: logging.info(f"{label} pressed")


class Keypad:
    buttons: dict[str, SyntheticButton]

    def __init__(self):
        with open('pinout.json') as f:
            pins = json.load(f)['keypad_bcm_pins']

        self.matrix = KeyMatrix(
            [Pin(p) for p in pins['rows']],
            [Pin(p) for p in pins['cols']]
        )
        self._buttons = [SyntheticButton(label) for label in BUTTON_LABELS]
        self.buttons = {button.label: button for button in self._buttons}

    async def run(self):
        try:
            while True:
                event = self.matrix.events.get()
                if event and event.pressed:
                    self._buttons[event.key_number].press()
                await asyncio.sleep(.001)
        finally:
            logging.exception('Keypad stopped')


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    event_loop = asyncio.get_event_loop()
    event_loop.create_task(Keypad().run())
    event_loop.run_forever()
