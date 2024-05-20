from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

import server
from kvm import KVM
from lcd import LCD
from menu import Menu
from pad import Keypad

keypad = Keypad()
lcd = LCD()
ui = Menu(keypad, KVM(), LCD())


@asynccontextmanager
async def lifespan(_: FastAPI):
    await keypad.run()


app = FastAPI(lifespan=lifespan)
server.state.lcd = lcd
app.include_router(server.router)

if __name__ == '__main__':
    uvicorn.run(
        app,
        host='0.0.0.0',
        port=1602,
        workers=1,
        limit_concurrency=1
    )
