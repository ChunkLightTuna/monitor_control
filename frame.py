import uuid
from dataclasses import dataclass, field
from typing import Callable, Dict
from uuid import UUID

from kvm import KVM
from lcd import Msg, LCD
from pad import BUTTON_LABELS


@dataclass
class Frame:
    msg: Msg
    key: UUID = field(default_factory=uuid.uuid4)
    button_funs: Dict[str, Callable[[], None]] = field(default_factory=dict)
    active: bool = False

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False


class Menu:
    kvm: KVM
    lcd: LCD

    def prev_menu(self):
        pass

    def next_menu(self):
        pass

    def msg(self, msg: Msg | str) -> str:
        pass

    def msg_ephemeral(self, msg: Msg | str, seconds=5):
        pass

    def numerical_input(self, msg: str, fun: Callable[[int], None], percent=True):
        pass

    def push(self, frame: Frame) -> str:
        pass

    def pop(self, key: str = None):
        pass


class MenuFrame(Frame):
    def __init__(
            self,
            menu: Menu,
            msg: Msg
    ):
        super().__init__(msg=msg)
        for b in BUTTON_LABELS:
            match b:
                case '2':
                    self.button_funs[b] = menu.prev_menu
                case '8':
                    self.button_funs[b] = menu.next_menu
                case '*':
                    self.button_funs[b] = menu.pop
                case _:  # for closure label is on left
                    self.button_funs[b] = lambda m=f"{b} unmapped": menu.msg_ephemeral(m, .5)


class MainMenuFrame(MenuFrame):
    def __init__(self, menu: Menu):
        super().__init__(menu, Msg('Main Menu').add_arrows())
        self.button_funs['A'] = lambda: menu.numerical_input('SET VOLUME', menu.kvm.volume)
        self.button_funs['B'] = lambda: menu.numerical_input("SET BRIGHTNESS", menu.kvm.brightness)
        self.button_funs['C'] = lambda: menu.msg_ephemeral(Msg('DISPLAY:', menu.kvm.prev(menu.lcd)))
        self.button_funs['D'] = lambda: menu.msg_ephemeral(Msg('DISPLAY:', menu.kvm.next(menu.lcd)))
