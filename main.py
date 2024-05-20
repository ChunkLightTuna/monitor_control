import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

import server
from kvm import KVM
from lcd import LCD
from menu import Menu
from pad import Keypad

keypad = Keypad()
lcd = LCD()
menu = Menu(keypad, KVM(), lcd)


@asynccontextmanager
async def lifespan(_: FastAPI):
    keypad_task = asyncio.create_task(keypad.run())
    yield
    keypad_task.cancel()


app = FastAPI(lifespan=lifespan, menu=menu)
app.include_router(server.router)

if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        app,
        host='0.0.0.0',
        port=1602
    )
