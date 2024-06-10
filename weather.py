import asyncio
import logging
import os
from datetime import datetime
from time import time

import httpx

from frame import MenuFrame, Menu
from lcd import FAHRENHEIT, MOON, SUN, Align, Msg

directions = [
    'N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'
]


def wind_dir(degrees: int) -> str:
    return next(d for i, d in enumerate(directions) if i * 22.5 >= degrees - 11.25)


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
            datetime.now().strftime('%I:%M%p').lstrip('0').ljust(7),
            'Weather Loading', Align.LEFT, Align.RIGHT
        )

        super().__init__(menu, msg)

    def todays_forecast(self):
        fore = httpx.get(self.forecast_url).json()
        today = datetime.now().day
        return [f for f in fore['list'] if datetime.fromtimestamp(int(f['dt'])).day == today]

    def update(self):
        res = httpx.get(self.current_url)
        if res.is_success:
            w = res.json()
            now = datetime.now()
            current_time = now.strftime('%I:%M%p').lstrip('0')
            conditions = f"{round(w['main']['temp'])}{FAHRENHEIT}{w['weather'][0]['main']}"[:10]
            wind = f"{round(w['wind']['speed'])}mph{wind_dir(w['wind']['deg'])}"

            sun_ts, sun_symbol = (
                w['sys']['sunset'], MOON
            ) if (w['sys']['sunrise'] < now.timestamp() < w['sys']['sunset']) else (
                w['sys']['sunrise'], SUN
            )

            sun_time = datetime.fromtimestamp(sun_ts)
            sun = f"{sun_symbol}{sun_time.strftime('%I:%M%p').lstrip('0')}"
            padding_1 = 16 - len(conditions)
            padding_2 = 16 - len(sun)
            self.msg = Msg(
                f'{current_time.ljust(padding_1)}{conditions}',
                f'{wind.ljust(padding_2)}{sun}'
            )
        else:
            self.msg = Msg('Failed to Pull', 'Weather Data', Align.CENTER, Align.CENTER)

    async def run(self):
        try:
            while True:
                await asyncio.sleep(60 - time() % 60)
                now = datetime.now()
                if self.active:
                    if now.minute % 15:
                        current_time = now.strftime('%I:%M%p').lstrip('0').ljust(7)
                        self.msg.line_one = f'{current_time}{self.msg.line_one[7:]}'
                    else:
                        self.update()

                    self.lcd.msg(self.msg)
        finally:
            logging.exception('Weather stopped')
