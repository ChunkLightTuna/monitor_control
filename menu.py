import asyncio
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Callable

import httpx

from kvm import KVM
from lcd import Msg, Align, LCD, FAHRENHEIT, SUN, MOON
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

        self.cur = 0
        self.submenus = []

        def prev_menu():
            self.cur = (self.cur - 1) % len(self.submenus)
            self.submenus[self.cur]()

        def next_menu():
            self.cur = (self.cur + 1) % len(self.submenus)
            self.submenus[self.cur]()

        def base():
            for b in self.buttons.values():
                b.press = lambda msg=f"{b.label} unmapped": self.msg_ephemeral(msg, .5)  # for closure label is on left
            self.buttons['2'].press = prev_menu
            self.buttons['8'].press = next_menu
            self.buttons['*'].press = self.pop

        def main_menu(init=False):
            base()
            self.buttons['A'].press = lambda: self.numerical_input('SET VOLUME', self.kvm.volume)
            self.buttons['B'].press = lambda: self.numerical_input("SET BRIGHTNESS", self.kvm.brightness)
            self.buttons['C'].press = lambda: self.msg_ephemeral(Msg('DISPLAY:', self.kvm.prev(self.lcd)))
            self.buttons['D'].press = lambda: self.msg_ephemeral(Msg('DISPLAY:', self.kvm.next(self.lcd)))
            self.msg(Msg('Main Menu').add_arrows(), push=init)

        self.submenus.append(main_menu)

        weather_key = os.environ.get('OPEN_WEATHER_API_KEY')
        if weather_key:
            lat = os.environ.get('LAT')
            lon = os.environ.get('LON')
            url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={weather_key}&units=imperial"
            directions = [
                'N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'
            ]

            def wind_dir(degrees: int):
                return next(d for i, d in enumerate(directions) if i * 22.5 >= degrees - 11.25)

            def weather():
                base()
                res = httpx.get(url)
                if res.is_success:
                    w = res.json()
                    now = datetime.now()

                    current_time = now.strftime('%I:%M%p').lstrip('0')
                    conditions = f"{round(w['main']['temp'])}{FAHRENHEIT} {w['weather'][0]['main']}"
                    wind = f"{round(w['wind']['speed'])}mph {wind_dir(w['wind']['deg'])}"

                    sun_ts = w['sys']['sunrise']
                    if now.timestamp() > sun_ts:
                        sun_ts = w['sys']['sunset']
                        sun_symbol = MOON
                    else:
                        sun_symbol = SUN
                    sun_time = datetime.fromtimestamp(sun_ts)
                    sun = f"{sun_symbol}{sun_time.strftime('%I:%M%p').lstrip('0')}"

                    padding_1 = 16 - len(conditions)
                    padding_2 = 16 - len(sun)
                    msg = Msg(
                        f'{current_time.ljust(padding_1)}{conditions}',
                        f'{wind.ljust(padding_2)}{sun}'
                    )
                else:
                    msg = Msg('Failed to Pull', 'Weather Data', Align.CENTER, Align.CENTER)

                self.lcd.msg(msg)

            weather_index = len(self.submenus)
            self.submenus.append(weather)
            main_menu(init=True)

            async def update_weather():
                while True:
                    now = datetime.now()
                    await asyncio.sleep(60 - now.timestamp() % 60)
                    if self.cur == weather_index:
                        if now.minute % 30:
                            current_time = now.strftime('%I:%M%p').lstrip('0').ljust(7)
                            self.stack[0].msg.line_one = f'{current_time}{self.stack[0].msg.line_one[7:]}'
                            self.lcd.msg(self.stack[0].msg)
                        else:
                            weather()

            asyncio.new_event_loop().run_until_complete(update_weather())

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
