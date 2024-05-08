#!/usr/bin/python3

import os
import subprocess
from signal import pause

from gpiozero import Button

button = Button(17)


class Monitor:
    def __init__(self, log=print):
        self.display_1 = (os.getenv('DISPLAY_1_LABEL'), f"0x{os.getenv('DISPLAY_1_ID')}")
        self.display_2 = (os.getenv('DISPLAY_2_LABEL'), f"0x{os.getenv('DISPLAY_2_ID')}")
        self.log = log

    def switch(self, device):
        self.log(f"DISPLAY:\n  {device[0]}")
        subprocess.run(["ddcutil", "setvcp", "0x60", device[1]])

    def brightness(self, b: int):
        b = str(max(min(b, 100), 0))
        self.log(f'BRIGHTNESS:\n  {b}%')
        subprocess.run(["ddcutil", "setvcp", "0x10", b])

    def volume(self, v: int):
        v = str(max(min(v, 100), 0))
        self.log(f'VOLUME:\n  {v}%')
        subprocess.run(["ddcutil", "setvcp", "0x62", v])

    def kvm_start(self):
        self.log("kvm start")
        button.when_released = lambda: self.switch(self.display_1)
        button.when_pressed = lambda: self.switch(self.display_2)

    def kvm_stop(self):
        self.log("kvm stop")
        button.when_released = lambda: None
        button.when_pressed = lambda: None


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    monitor = Monitor()
    monitor.kvm_start()
    pause()
