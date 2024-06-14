import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

import server
from lcd import Msg, Align
from main_menu import MainMenu
from pad import Keypad

keypad = Keypad()
menu = MainMenu(keypad)


@asynccontextmanager
async def lifespan(_: FastAPI):
    menu.msg_ephemeral(Msg('Monitor', 'Control', align_two=Align.RIGHT))
    tasks = [
        asyncio.create_task(keypad.run(), name='Keypad'),
        asyncio.create_task(menu.run(), name='Menu')
    ]

    yield
    menu.msg(Msg('Shutting', 'Down', Align.CENTER, Align.CENTER))
    for task in tasks:
        task.cancel()


app = FastAPI(lifespan=lifespan, menu=menu)
app.include_router(server.router)