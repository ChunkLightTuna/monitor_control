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
        open_weather_url = "https://api.openweathermap.org/data/2.5"
        url_params = f"lat={lat}&lon={lon}&appid={weather_key}&units=imperial"
        self.current_url = f"{open_weather_url}/weather?{url_params}"
        self.forecast_url = f"{open_weather_url}/forecast?{url_params}"

        msg = Msg(
            time_str(datetime.now()).ljust(7),
            'Weather Loading', Align.LEFT, Align.RIGHT
        )
        asyncio.create_task(self.update_all())
        super().__init__(menu, msg)

    def activate(self):
        super().activate()
        asyncio.create_task(self.update_all())

    def todays_forecast(self):
        fore = httpx.get(self.forecast_url).json()
        today = datetime.now().day
        return [f for f in fore['list'] if datetime.fromtimestamp(int(f['dt'])).day == today]

    async def update_all(self):
        async with httpx.AsyncClient() as client:
            res = await client.get(self.current_url)
            if res.is_success:
                w = res.json()
                now = datetime.now()
                current_time = time_str(now)
                conditions = f"{round(w['main']['temp'])}{FAHRENHEIT}{w['weather'][0]['main']}"[:10]
                wind = f"{round(w['wind']['speed'])}mph{wind_dir(w['wind']['deg']) if int(w['wind']['speed']) else ''}"

                sun_ts, sun_symbol = (
                    w['sys']['sunset'], MOON
                ) if (w['sys']['sunrise'] < now.timestamp() < w['sys']['sunset']) else (
                    w['sys']['sunrise'], SUN
                )

                sun_time = datetime.fromtimestamp(sun_ts)
                sun = f"{sun_symbol}{time_str(sun_time)}"
                padding_1 = 16 - len(conditions)
                padding_2 = 16 - len(sun)
                self.msg = Msg(
                    f'{current_time.ljust(padding_1)}{conditions}',
                    f'{wind.ljust(padding_2)}{sun}'
                )
            else:
                logging.exception(pformat(res.__dict__))
                self.msg = Msg('Failed to Pull', 'Weather Data', Align.CENTER, Align.CENTER)

            if self.active:
                self.lcd.msg(self.msg)

    def update_time(self, dt: datetime):
        current_time = time_str(dt).ljust(7)
        self.msg.line_one = f'{current_time}{self.msg.line_one[7:]}'
        if self.active:
            self.lcd.msg(self.msg)

    async def run(self):
        try:
            while True:
                await asyncio.sleep(60 - time() % 60)
                now = datetime.now()
                if self.active:
                    if now.minute % 15:
                        self.update_time(now)
                    else:
                        await self.update_all()


        finally:
            logging.exception('Weather stopped')
