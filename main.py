import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

import server
from lcd import Msg, Align
from menu import Menu
from pad import Keypad

keypad = Keypad()
menu = Menu(keypad)


@asynccontextmanager
async def lifespan(_: FastAPI):
    menu.msg_ephemeral(Msg('Monitor', 'Control', align_two=Align.RIGHT))
    keypad_task = asyncio.create_task(keypad.run())
    yield
    menu.msg(Msg('Shutting', 'Down', Align.CENTER, Align.CENTER))
    keypad_task.cancel()


app = FastAPI(lifespan=lifespan, menu=menu)
app.include_router(server.router)
