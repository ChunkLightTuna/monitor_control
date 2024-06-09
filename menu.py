import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from typing import Callable, Dict, List
from uuid import UUID

from kvm import KVM
from lcd import LCD, Msg
from pad import Keypad, BUTTON_LABELS, SyntheticButton
from weather import Weather


@dataclass
class Frame:
    msg: Msg
    key: UUID = field(default_factory=uuid.uuid4)
    button_funs: Dict[str:Callable[[], None]] = field(default_factory=dict)
    active: bool = False


class Menu:
    def __init__(self, keypad: Keypad):
        self.buttons: dict[str, SyntheticButton] = keypad.buttons
        self.kvm = KVM()
        self.lcd = LCD()

        self.cur = 0
        main_menu = MainMenuFrame(active=True)
        self.stack: List[Frame] = [main_menu]
        self.weather = Weather()
        self.submenus: List[Frame] = [main_menu, self.weather]

        self.apply()

    async def run(self):
        await asyncio.gather(self.weather.run())

    def prev_menu(self):
        self.cur = (self.cur - 1) % len(self.submenus)
        self.apply(self.submenus[self.cur])

    def next_menu(self):
        self.cur = (self.cur + 1) % len(self.submenus)
        self.apply(self.submenus[self.cur])

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
        self.stack[-1].active = False
        frame.active = True
        self.stack.append(frame)
        return frame.key

    def pop(self, key: str = None):
        logging.info(f'pop {key=}')
        if len(self.stack) > 1:
            if key:
                idx = next((i for (i, s) in enumerate(self.stack) if key == s.key), None)
                if idx:
                    self.stack[idx].active = False
                    del self.stack[idx]
                    if idx != len(self.stack):
                        return  # don't need to refresh UI if pulling from middle of stack
            else:
                self.stack[-1].active = False
                self.stack.pop()

        self.stack[-1].active = True
        self.apply()


class MenuFrame(Frame):
    def __init__(
            self,
            menu: Menu,
            msg: Msg,
            key: uuid.UUID = None,
            button_funs: Dict[str, Callable[[], None]] = None,
    ):
        super().__init__(msg, key, button_funs, True)
        for b in BUTTON_LABELS:
            match b:
                case '2':
                    button_funs[b] = menu.prev_menu
                case '8':
                    button_funs[b] = menu.next_menu
                case '*':
                    button_funs[b] = menu.pop
                case _:  # for closure label is on left
                    button_funs[b] = lambda m=f"{b} unmapped": menu.msg_ephemeral(m, .5)


class MainMenuFrame(MenuFrame):
    def __init__(self, menu: Menu):
        super().__init__(menu, Msg('Main Menu').add_arrows())
        self.button_funs['A'] = lambda: menu.numerical_input('SET VOLUME', menu.kvm.volume)
        self.button_funs['B'] = lambda: menu.numerical_input("SET BRIGHTNESS", menu.kvm.brightness)
        self.button_funs['C'] = lambda: menu.msg_ephemeral(Msg('DISPLAY:', menu.kvm.prev(menu.lcd)))
        self.button_funs['D'] = lambda: menu.msg_ephemeral(Msg('DISPLAY:', menu.kvm.next(menu.lcd)))
