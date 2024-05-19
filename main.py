import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

import server
from kvm import KVM
from lcd import LCD
from menu import Menu
from pad import Keypad

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

keypad = Keypad()
lcd = LCD()
ui = Menu(keypad, KVM(), LCD())


@asynccontextmanager
async def lifespan(_: FastAPI):
    keypad.run()


app = FastAPI(lifespan=lifespan)
app.state.lcd = lcd
app.include_router(server.router)

if __name__ == '__main__':
    uvicorn.run(app, port=1602)
