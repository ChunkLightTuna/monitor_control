import asyncio
import logging
from collections import deque
from contextlib import asynccontextmanager
from time import monotonic

from fastapi import FastAPI

import server
from lcd import Msg, Align
from main_menu import MainMenu
from pad import Keypad

logging.basicConfig(level=logging.INFO)
logging.info("""
    __  ___   ____     _   __    ____  ______   ____     ____           ______   ____     _   __  ______    ____    ____     __ 
   /  |/  /  / __ \   / | / /   /  _/ /_  __/  / __ \   / __ \         / ____/  / __ \   / | / / /_  __/   / __ \  / __ \   / / 
  / /|_/ /  / / / /  /  |/ /    / /    / /    / / / /  / /_/ /        / /      / / / /  /  |/ /   / /     / /_/ / / / / /  / /  
 / /  / /  / /_/ /  / /|  /   _/ /    / /    / /_/ /  / _, _/        / /___   / /_/ /  / /|  /   / /     / _, _/ / /_/ /  / /___
/_/  /_/   \____/  /_/ |_/   /___/   /_/     \____/  /_/ |_|         \____/   \____/  /_/ |_/   /_/     /_/ |_|  \____/  /_____/
                                                                                                                                
""")

keypad = Keypad()
menu = MainMenu(keypad)

MAX_INTERVAL = 30
RETRY_HISTORY = 3


# That is, stop after the 3rd failure in a 30 second moving window

def supervise(func, name=None, retry_history=RETRY_HISTORY, max_interval=MAX_INTERVAL):
    """Simple wrapper function that automatically tries to name tasks"""
    if name is None:
        if hasattr(func, '__name__'):  # raw func
            name = func.__name__
        elif hasattr(func, 'func'):  # partial
            name = func.func.__name__
    return asyncio.create_task(supervisor(func, retry_history, max_interval), name=name)


async def supervisor(func, retry_history=RETRY_HISTORY, max_interval=MAX_INTERVAL):
    """Takes a noargs function that creates a coroutine, and repeatedly tries
        to run it. It stops is if it thinks the coroutine is failing too often or
        too fast.
    """
    start_times = deque([float('-inf')], maxlen=retry_history)
    while True:
        start_times.append(monotonic())
        try:
            return await func()
        except asyncio.CancelledError:
            logging.exception(f'{func.__name__} cancelled.')
        except Exception as e:
            if min(start_times) > monotonic() - max_interval:
                raise e
            else:
                logging.exception(
                    f'{func.__name__} failed, will retry. Failed because:\n{str(e)}',
                    stack_info=True
                )


@asynccontextmanager
async def lifespan(_: FastAPI):
    menu.msg_ephemeral(Msg('Monitor', 'Control', align_two=Align.RIGHT))
    tasks = [
        supervise(keypad.run, name='Keypad'),
        supervise(menu.run, name='Menu')
    ]

    yield
    menu.msg(Msg('Shutting', 'Down', Align.CENTER, Align.CENTER))
    for task in tasks:
        task.cancel()


app = FastAPI(lifespan=lifespan, menu=menu)
app.include_router(server.router)
