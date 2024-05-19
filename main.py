import asyncio
import logging

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

asyncio.gather(keypad.run(), server.run(lcd))
