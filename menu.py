import asyncio
import logging
import os
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
        self.weather_key = os.environ.get('OPEN_WEATHER_API_KEY')
        logging.warning(self.weather_key)

        for b in self.buttons.values():
            b.press = lambda msg=f"{b.label} unmapped": self.msg_ephemeral(msg, .5)  # for closure label is on left
        self.buttons['2'].press = lambda: self.lcd.msg(Msg('lol', align_one=Align.CENTER))
        self.buttons['8'].press = lambda: self.lcd.msg(Msg('ggg', align_one=Align.CENTER))
        self.buttons['*'].press = self.pop
        self.buttons['A'].press = lambda: self.numerical_input('SET VOLUME', self.kvm.volume)
        self.buttons['B'].press = lambda: self.numerical_input("SET BRIGHTNESS", self.kvm.brightness)
        self.buttons['C'].press = lambda: self.msg_ephemeral(Msg('DISPLAY:', self.kvm.prev(self.lcd)))
        self.buttons['D'].press = lambda: self.msg_ephemeral(Msg('DISPLAY:', self.kvm.next(self.lcd)))
        self.msg(Msg('Main Menu').add_arrows())

    def msg(self, msg: Msg | str, push: bool = True) -> str | None:
        if isinstance(msg, str):
            msg = Msg(msg)

        self.lcd.msg(msg)
        if push:
            return self.push(msg)

    def msg_ephemeral(self, msg: Msg | str, seconds=5):
        async def inner(m, s):
            key = self.msg(m)
            await asyncio.sleep(s)
            self.pop(key)

        asyncio.create_task(inner(msg, seconds))

    def numerical_input(self, msg: str, fun: Callable[[int], None], percent=True):
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
                        num = f"{min(int(num), 100)}%"
                    stack_msg.line_two = f"""{num:>16}"""
                    self.msg(stack_msg, push=False)

                button.press = inner
            if button.label == '#':
                def commit():
                    fun(int(''.join(queue)))
                    self.pop()

                button.press = commit

        self.msg(msg)

    def push(self, msg: Msg):
        key = uuid.uuid4().hex
        logging.info(f'push {key=}')
        self.stack.append(Stack(
            key=key,
            msg=msg,
            button_labels_to_actions={button.label: button.press for button in self.buttons.values()}
        ))
        return key

    def pop(self, key: str = None):
        logging.info(f'pop {key=}')
        if len(self.stack) > 1:
            if key:
                idx = next((i for (i, s) in enumerate(self.stack) if key == s.key), None)
                if idx:
                    del self.stack[idx]
                    if idx != len(self.stack):
                        return  # don't need to refresh UI if pulling from middle of stack
            else:
                self.stack.pop()

        state = self.stack[-1]
        for (label, when_pressed) in state.button_labels_to_actions.items():
            self.buttons[label].press = when_pressed
        self.lcd.msg(state.msg)
