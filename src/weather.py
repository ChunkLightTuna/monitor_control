import asyncio
import logging
import os
from datetime import datetime
from pprint import pformat
from time import time

import httpx

from frame import MenuFrame, Menu
from lcd import Align, Msg, time_str
from patterns import FAHRENHEIT, MOON, SUN

directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']


def wind_dir(degrees: int) -> str:
    if degrees >= 360:
        degrees = degrees % 360
    return next(d for i, d in enumerate(directions) if abs(degrees - (i * 22.5)) % (360 - 11.25) < 11.25)


class Weather(MenuFrame):
    def __init__(self, menu: Menu):
        self.lcd = menu.lcd
        weather_key = os.environ.get('OPEN_WEATHER_API_KEY')
        lat = os.environ.get('LAT')
        lon = os.environ.get('LON')
        self.invalid = any(i is None for i in [weather_key, lat, lon])
        open_weather_url = "https://api.openweathermap.org/data"
        url_params = f"lat={lat}&lon={lon}&appid={weather_key}&units=imperial"
        self.current_url = f"{open_weather_url}/2.5/weather?{url_params}"
        self.forecast_url = f"{open_weather_url}/2.5/forecast?{url_params}"
        self.detailed_forecast_url = f"{open_weather_url}/3.0/onecall?{url_params}"

        self.temperature = ''
        self.conditions = ''
        self.sun = ''
        self.wind_speed = ''
        self.wind_dir = ''

        msg = Msg(
            time_str(datetime.now()),
            'Bad Weather Conf' if self.invalid else 'Weather Loading', Align.LEFT, Align.RIGHT
        )
        asyncio.create_task(self.update_weather())
        super().__init__(menu, msg)

    def activate(self):
        super().activate()
        asyncio.create_task(self.update_weather())

    def todays_forecast(self):
        fore = httpx.get(self.forecast_url).json()
        today = datetime.now().day
        return [f for f in fore['list'] if datetime.fromtimestamp(int(f['dt'])).day == today]

    async def update_weather(self):
        if self.invalid:
            return
        async with httpx.AsyncClient() as client:
            res = await client.get(self.current_url)
            now = datetime.now()
            if res.is_success:
                w = res.json()
                self.temperature = f"{round(w['main']['temp'])}{FAHRENHEIT}"
                self.conditions = w['weather'][0]['main']
                self.wind_speed = f"{round(w['wind']['speed'])}mph"
                self.wind_dir = wind_dir(w['wind']['deg']) if int(w['wind']['speed']) else ''

                sun_ts, sun_symbol = (
                    w['sys']['sunset'], MOON
                ) if (w['sys']['sunrise'] < now.timestamp() < w['sys']['sunset']) else (
                    w['sys']['sunrise'], SUN
                )
                self.sun = f"{sun_symbol}{time_str(datetime.fromtimestamp(sun_ts))}"
            else:
                logging.exception(pformat(res.__dict__))

            self.update_msg(now)

    async def get_forecast(self):
        async with httpx.AsyncClient() as client:
            res = await client.get(self.forecast_url)

    def update_msg(self, dt: datetime):
        ts = time_str(dt)
        s1 = max(0, 16 - (len(ts) + len(self.temperature) + len(self.conditions)))
        line_one = f"{ts}{' ' * (int(s1 / 2) + s1 % 2)}{self.temperature}{' ' * int(s1 / 2)}{self.conditions}"

        s2 = 16 - (len(self.wind_speed) + len(self.wind_dir) + len(self.sun))

        s21 = int(s2 > 1)
        s22 = s2 - s21
        line_two = f"{self.wind_speed}{' ' * s21}{self.wind_dir}{' ' * s22}{self.sun}"

        self.msg = Msg(line_one, line_two)
        if self.active:
            self.lcd.msg(self.msg)

    async def __call__(self):
        while True:
            await asyncio.sleep(60 - time() % 60)
            now = datetime.now()
            if self.active:
                if now.minute % 15:
                    self.update_msg(now)
                else:
                    await self.update_weather()
