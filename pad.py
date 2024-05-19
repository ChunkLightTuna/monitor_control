import asyncio
import json
import logging
from dataclasses import dataclass

from digitalio import Pin
from keypad import KeyMatrix


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
        '1', '2', '3', 'A',
        '4', '5', '6', 'B',
        '7', '8', '9', 'C',
        '*', '0', '#', 'D'
    ]

    def __init__(self):
        with open('pinout.json') as f:
            pins = json.load(f)['keypad_bcm_pins']

        self.matrix = KeyMatrix(
            [Pin(p) for p in pins['rows']],
            [Pin(p) for p in pins['cols']]
        )
        self.buttons = [SyntheticButton(b) for b in self.labels]

    def run(self):
        event_loop = asyncio.get_event_loop()

        async def f():
            while True:
                event = self.matrix.events.get()
                if event and event.pressed:
                    self.buttons[event.key_number].press()
                await asyncio.sleep(.001)

        event_loop.create_task(f())
        event_loop.run_forever()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    Keypad().run()
