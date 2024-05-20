import asyncio
import logging
import uuid
from dataclasses import dataclass
from typing import Dict, Callable

from kvm import KVM
from lcd import Message, Align, LCD
from pad import Keypad


@dataclass
class Stack:
    key: str
    title: str
    button_labels_to_actions: Dict[str, Callable[[], None]]


class Menu:
    def __init__(self, keypad: Keypad, kvm: KVM, lcd: LCD):
        self.stack: list[Stack] = []
        self.title = Message('Main Menu').add_arrows()
        self.buttons = keypad.buttons
        self.kvm = kvm
        self.lcd = lcd
        self.lcd.msg(self.title)

        for b in self.buttons.values():
            b.press = lambda: self.lcd.msg(f"{b.label} unmapped")
        self.buttons['2'].press = lambda: self.lcd.msg('lol', align=Align.CENTER)
        self.buttons['8'].press = lambda: self.lcd.msg('ggg', align=Align.CENTER)
        self.buttons['*'].press = self.pop
        self.buttons['A'].press = lambda: self.audio_mode('A')
        self.buttons['B'].press = lambda: self.brightness_mode('B')
        self.buttons['C'].press = lambda: lcd.msg(Message('DISPLAY:', self.kvm.prev(lcd)))
        self.buttons['D'].press = lambda: lcd.msg(Message('DISPLAY:', self.kvm.next(lcd)))
        self.push()

    def set_title(self, m: Message | str):
        if isinstance(m, str):
            m = Message(m)

        self.title = m
        self.lcd.msg(m)

    async def tmp_mode(self, msg: Message):
        self.set_title(msg)
        key = self.push()
        asyncio.sleep(5)
        self.pop(key)

    def audio_mode(self, button_label: str):
        def set_audio(a: str):
            self.lcd.msg(Message('VOLUME:', f'{a}%'))
            self.kvm.volume(int(a))
            self.pop()

        self.handle_input("SET VOLUME", button_label, set_audio)

    def brightness_mode(self, button_label: str):
        def set_brightness(b: str):
            self.lcd.msg(Message('BRIGHTNESS:', f'{b}%'))
            self.kvm.brightness(int(b))
            self.pop()

        self.handle_input("SET BRIGHTNESS", button_label, set_brightness)

    def handle_input(self, title: str, button_label: str, fun: callable):
        queue = []
        for button in self.buttons.values():
            if button.label.isdigit():
                cur_label = button.label
                button.press = lambda: queue.append(cur_label)
            if button.label == '#':
                button.press = lambda: fun(''.join(queue))

        self.buttons[button_label].press = self.pop
        self.set_title(title)
        self.push()

    def push(self):
        key = uuid.uuid4().hex
        logging.warning(f'Push {key=} {self.title=}')

        self.stack.append(Stack(
            key=key,
            title=self.title,
            button_labels_to_actions={button.label: button.press for button in self.buttons.values()}
        ))
        return key

    def pop(self, key: str = None):
        logging.info(f'Pop {key=} {self.title=}')
        print(f'Pop {key=} {self.title=}')

        if len(self.stack) > 1:
            if key:
                idx = next((i for (i, s) in enumerate(self.stack) if key == s.key), None)
                if idx:
                    del self.stack[idx]
            else:
                self.stack.pop()

        state = self.stack[-1]
        for (label, when_pressed) in state.button_labels_to_actions.items():
            self.buttons[label].press = when_pressed
        self.set_title(state.title)
