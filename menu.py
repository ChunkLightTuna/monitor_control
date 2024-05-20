import asyncio
import logging
import uuid
from dataclasses import dataclass
from typing import Dict, Callable

from kvm import KVM
from lcd import Msg, Align, LCD
from pad import Keypad


@dataclass
class Stack:
    key: str
    msg: Msg
    button_labels_to_actions: Dict[str, Callable[[], None]]


class Menu:
    def __init__(self, keypad: Keypad):
        self.stack: list[Stack] = []
        self.buttons = keypad.buttons
        self.kvm = KVM()
        self.lcd = LCD()

        for b in self.buttons.values():
            b.press = lambda msg=f"{b.label} unmapped": self.msg_ephemeral(msg, 1)  # closure
        self.buttons['2'].press = lambda: self.lcd.msg(Msg('lol', align_one=Align.CENTER))
        self.buttons['8'].press = lambda: self.lcd.msg(Msg('ggg', align_one=Align.CENTER))
        self.buttons['*'].press = self.pop
        self.buttons['A'].press = lambda: self.audio_mode('A')
        self.buttons['B'].press = lambda: self.brightness_mode('B')
        self.buttons['C'].press = lambda: self.lcd.msg(Msg('DISPLAY:', self.kvm.prev(self.lcd)))
        self.buttons['D'].press = lambda: self.lcd.msg(Msg('DISPLAY:', self.kvm.next(self.lcd)))
        self.msg(Msg('Main Menu').add_arrows())

    def msg(self, msg: Msg | str, push: bool = True) -> str | None:
        if isinstance(msg, str):
            msg = Msg(msg)

        self.lcd.msg(msg)
        if push:
            return self.push(msg)

    async def async_msg_ephemeral(self, msg: Msg | str, seconds=5):
        logging.warning(f'c:{msg=}')
        key = self.msg(msg)
        logging.warning(f'd:{msg=}')
        await asyncio.sleep(seconds)
        logging.warning(f'e:{msg=}')
        self.pop(key)
        logging.warning(f'f:{msg=}')

    def msg_ephemeral(self, msg: Msg | str, seconds=5):
        logging.warning(f'a:{msg=}')
        asyncio.get_event_loop().run_until_complete(self.async_msg_ephemeral(msg, seconds))
        logging.warning(f'b:{msg=}')

    def audio_mode(self, button_label: str):
        def inner(a: int):
            self.lcd.msg(Msg('VOLUME:', f'{a}%'))
            self.kvm.volume(a)
            self.pop()

        self.numerical_input("SET VOLUME", button_label, inner)

    def brightness_mode(self, button_label: str):
        def inner(b: int):
            self.lcd.msg(Msg('BRIGHTNESS:', f'{b}%'))
            self.kvm.brightness(b)
            self.pop()

        self.numerical_input("SET BRIGHTNESS", button_label, inner)

    def numerical_input(self, msg: str, button_label: str, fun: Callable[[int], None], percent=True):
        queue = []

        # since self.msg at the bottom of this function adds to the stack, len() will refer to that element
        cur_stack = len(self.stack)

        for button in self.buttons.values():
            if button.label.isdigit():
                def inner(cur_label=button.label):  # default arg is required to wrap the button label in a closure
                    queue.append(cur_label)
                    stack_msg = self.stack[cur_stack].msg
                    num = ''.join(queue)
                    if percent:
                        num = f"{max(int(num), 100)}%"
                    stack_msg.line_two = f"""{num:>16}"""
                    self.msg(stack_msg, push=False)
                    if percent and len(num) >= 2 and num != '10':
                        fun(int(num))

                button.press = inner
            if button.label == '#':
                button.press = lambda: fun(int(''.join(queue)))

        self.buttons[button_label].press = self.pop
        self.msg(msg)

    def push(self, msg: Msg):
        key = uuid.uuid4().hex

        self.stack.append(Stack(
            key=key,
            msg=msg,
            button_labels_to_actions={button.label: button.press for button in self.buttons.values()}
        ))
        return key

    def pop(self, key: str = None):
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
        self.lcd.msg(state.msg)
