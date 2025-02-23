import asyncio
import logging
from typing import Callable, List

from frame import Frame, Menu, MenuFrame
from kvm import KVM
from lcd import LCD, Msg
from pad import Keypad, SyntheticButton
from weather import Weather


class MainMenu(Menu):
    def __init__(self, keypad: Keypad):
        self.buttons: dict[str, SyntheticButton] = keypad.buttons
        self.kvm = KVM()
        self.lcd = LCD()

        self.cur = 0
        self.submenus: List[MenuFrame] = [
            Weather(self),
            MenuFrame(self, Msg('Main Menu').add_arrows())
        ]
        self.stack: List[Frame] = [self.submenus[0]]
        self.stack[0].activate()
        self.apply()

    async def run(self):
        await asyncio.gather(*[f() for f in [*self.stack, *self.submenus] if callable(f)])

    def prev_menu(self):
        self.submenus[self.cur].deactivate()
        self.cur = (self.cur - 1) % len(self.submenus)
        self.apply(self.submenus[self.cur])
        self.submenus[self.cur].activate()

    def next_menu(self):
        self.submenus[self.cur].deactivate()
        self.cur = (self.cur + 1) % len(self.submenus)
        self.apply(self.submenus[self.cur])
        self.submenus[self.cur].activate()

    def msg(self, msg: Msg | str) -> str:
        if isinstance(msg, str):
            msg = Msg(msg)

        self.lcd.msg(msg)
        return self.push(Frame(msg))

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
                    self.lcd.msg(stack_msg)

                button.press = inner
            if button.label == '#':
                def commit():
                    fun(int(''.join(queue)))
                    self.pop()

                button.press = commit

        self.msg(msg)

    def apply(self, frame: Frame = None):
        if not frame:
            frame = self.stack[-1]

        for label, fun in frame.button_funs.items():
            self.buttons[label].press = fun
        self.lcd.msg(frame.msg)

    def push(self, frame: Frame) -> str:
        self.stack[-1].deactivate()
        frame.activate()
        self.stack.append(frame)
        return frame.key

    def pop(self, key: str = None):
        logging.info(f'pop {key=}')
        if len(self.stack) > 1:
            if key:
                idx = next((i for (i, s) in enumerate(self.stack) if key == s.key), None)
                if idx:
                    self.stack[idx].deactivate()
                    del self.stack[idx]
                    if idx != len(self.stack):
                        return  # don't need to refresh UI if pulling from middle of stack
            else:
                self.stack[-1].deactivate()
                self.stack.pop()

        self.stack[-1].activate()
        self.apply()
