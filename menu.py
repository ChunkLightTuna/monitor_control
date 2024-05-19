import logging

from keypad import Keypad
from lcd import LCD, Message, Align
from main import kvm


class Menu:
    def __init__(self, lcd: LCD, keypad: Keypad):
        self.stack = []
        self.title = Message('Main Menu').add_arrows()
        lcd.msg(self.title)
        self.lcd = lcd
        self.buttons = keypad.buttons

        for b in self.buttons.values():
            b.press = lambda: lcd.msg(f"{b.label} unmapped")
        self.buttons['2'].press = lambda: lcd.msg('lol', align=Align.CENTER)
        self.buttons['8'].press = lambda: lcd.msg('ggg', align=Align.CENTER)
        self.buttons['*'].press = self.pop
        self.buttons['A'].press = lambda: self.audio_mode('A')
        self.buttons['B'].press = lambda: self.brightness_mode('B')
        self.buttons['C'].press = lambda: kvm.prev()
        self.buttons['D'].press = lambda: kvm.next()

    def set_title(self, m: Message | str):
        if isinstance(m, str):
            m = Message(m)

        self.title = m
        self.lcd.msg(m)

    def audio_mode(self, label: str):
        self.push()
        self.set_title("SET VOLUME")

        def set_audio(a):
            kvm.volume(int(a))
            self.pop()

        self.handle_input(label, set_audio)

    def brightness_mode(self, label: str):
        self.push()
        self.set_title("SET BRIGHTNESS")

        def set_brightness(b):
            kvm.brightness(int(b))
            self.pop()

        self.handle_input(label, set_brightness)

    def handle_input(self, label: str, fun: callable):
        queue = []
        for button in self.buttons.values():
            if button.label.isdigit():
                button.press = lambda i=button.label: queue.append(i)
            if button.label == '#':
                button.press = lambda: fun(''.join(queue))

        self.buttons[label].press = self.pop

    def push(self):
        logging.debug("push")
        self.stack.append((
            dict([(button.label, button.press) for button in self.buttons.values()]),
            self.title
        ))

    def pop(self):
        logging.debug("pop")
        if self.stack:
            (actions, title) = self.stack.pop()
            for (label, when_pressed) in actions.items():
                self.buttons[label].press = when_pressed
            self.set_title(title)
        else:
            self.set_title(self.title)
