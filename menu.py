import asyncio
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
            b.press = lambda: self.lcd.msg(f"{b.label} unmapped")
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
            return self.push()

    async def msg_ephemeral(self, msg: Msg | str) -> str | None:
        if isinstance(msg, str):
            msg = Msg(msg)

        self.lcd.msg(msg)
        key = self.push()

        await asyncio.sleep(5)
        self.pop(key)

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

    def numerical_input(self, msg: str, button_label: str, fun: Callable[[int], None]):
        queue = []

        # since self.msg at the bottom of this function adds to the stack, len() will refer to that element
        cur_stack = len(self.stack)

        for button in self.buttons.values():
            if button.label.isdigit():
                cur_label = button.label

                def inner():
                    queue.append(cur_label)
                    stack_msg = self.stack[cur_stack].msg
                    stack_msg.line_two = f"{''.join(queue):>16}"
                    self.msg(stack_msg, push=False)

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
