#!/usr/bin/python3
import json
import subprocess
from dataclasses import dataclass
from signal import pause

from gpiozero import Button

button = Button(17)


@dataclass
class Display:
    id: str
    label: str


class Monitor:
    def __init__(self, log=print):
        with open('pins.json') as f:
            displays = json.load(f)['displays'] or None

        if self.displays:
            self.displays = [Display(**display) for display in displays]
        else:
            capabilities = subprocess.run(["ddcutil", "capabilities"], stdout=subprocess.PIPE).stdout.decode('utf-8')
            self.displays = [
                Display(id=f"0x{j[0]}", label=j[1])
                for j in [
                    k.strip().split(': ')
                    for k in capabilities
                             .split("Feature: 60 (Input Source)\n", 1)[1]
                             .split("\n   Feature: 62 (Audio speaker volume)", 1)[0]
                             .split('\n')[1:]
                ]
            ]

        current_id = '0' + subprocess.run(
            ["ddcutil", "getvcp", "0x60", "--terse"],
            stdout=subprocess.PIPE
        ).stdout.decode("utf-8").strip().split(" ")[-1]

        self.cur = next((idx for idx, d in enumerate(self.displays) if d.id == current_id), 0)

        self.log = log

    def next(self):
        self.cur = (self.cur + 1) % len(self.displays)
        self.switch(self.displays[self.cur])

    def prev(self):
        self.cur = (self.cur - 1) % len(self.displays)
        self.switch(self.displays[self.cur])

    def switch(self, display: Display):
        self.log(f"DISPLAY:\n  {display.label}")
        subprocess.run(["ddcutil", "setvcp", "0x60", display.id])

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
        button.when_released = lambda: self.switch(self.displays[0])
        button.when_pressed = lambda: self.switch(self.displays[1])

    def kvm_stop(self):
        self.log("kvm stop")
        button.when_released = lambda: None
        button.when_pressed = lambda: None


if __name__ == "__main__":
    monitor = Monitor()
    monitor.kvm_start()
    pause()
