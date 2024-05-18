import json
import subprocess
from dataclasses import dataclass
from signal import pause


@dataclass
class Display:
    id: str
    label: str


class Monitor:
    def __init__(self, log=print):
        with open('pinout.json') as f:
            pinout = json.load(f)

        # When you get around to using a KVM again
        # self.kvm_in = DigitalInputDevice(pinout['kvm']['in'])  # wire to KVM VGA ground/float
        # self.kvm_out = DigitalOutputDevice(pinout['kvm']['out'])  # wire to KVM button

        if 'displays' in pinout:
            self.displays = [Display(**display) for display in pinout['displays']]
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


if __name__ == "__main__":
    monitor = Monitor()
    pause()
