import asyncio
import logging

import server
from keypad import Keypad
from kvm import KVM
from lcd import LCD
from menu import Menu

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

keypad = Keypad()
lcd = LCD()
ui = Menu(keypad, KVM(), LCD())

asyncio.gather(keypad.run(), server.run(lcd))
