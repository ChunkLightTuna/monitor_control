import logging

import display
import server
from keypad import Pad
from kvm import Monitor

pad = Pad()
buttons = pad.buttons
lcd = display.lcd


def msg(s):
    logging.debug(f"<{s}>")
    lcd.clear()
    c = s.replace('\\', display.backslash)
    lcd.message = c


def msg_gen(s):
    return lambda: msg(s)


monitor = Monitor(msg)


class UI:
    def __init__(self):
        self.stack = []
        self.title = f"Main Menu     2{display.up_arrow}\n              8{display.down_arrow}"
        msg(self.title)

    def set_title(self, title):
        self.title = title
        msg(title)

    def audio_mode(self, label):
        self.push()
        self.set_title("SET VOLUME")

        def set_audio(a):
            monitor.volume(int(a))
            self.pop()

        self.handle_input(label, set_audio)

    def brightness_mode(self, label):
        self.push()
        self.set_title("SET BRIGHTNESS")

        def set_brightness(b):
            monitor.brightness(int(b))
            self.pop()

        self.handle_input(label, set_brightness)

    def handle_input(self, label, fun):
        queue = []
        for button in buttons.values():
            if button.label.isdigit():
                button.when_pressed = lambda i=button.label: queue.append(i)
            if button.label == '#':
                button.when_pressed = lambda: fun(''.join(queue))

        buttons[label].when_pressed = self.pop

    def push(self):
        logging.debug("push")
        self.stack.append((
            dict([(button.label, button.when_pressed) for button in buttons.values()]),
            self.title
        ))

    def pop(self):
        logging.debug("pop")
        if self.stack:
            (actions, title) = self.stack.pop()
            for (label, when_pressed) in actions.items():
                buttons[label].when_pressed = when_pressed
            self.set_title(title)
        else:
            self.set_title(self.title)


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger()

    monitor.kvm_start()

    for b in buttons.values():
        b.when_pressed = msg_gen(f"{b.label} unmapped")

    ui = UI()
    buttons['2'].when_pressed = msg_gen("      lol")
    buttons['8'].when_pressed = msg_gen("      ggg")
    buttons['*'].when_pressed = ui.pop
    buttons['A'].when_pressed = lambda: ui.audio_mode('A')
    buttons['B'].when_pressed = lambda: ui.brightness_mode('B')
    buttons['C'].when_pressed = lambda: monitor.switch(monitor.prev())
    buttons['D'].when_pressed = lambda: monitor.switch(monitor.next())

    pad.start()

    server.run(msg)

    # pause()
