# maintainRange.py
# Corbin Weiss
# created 2023-6-5

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pasco import PascoBot
import time
import math
"""
This program will make the PASCO bot maintain a given distance
from an object (e.g. your hand) by moving forward and backward
"""


def maintain(target_distance):
    bot = PascoBot()
    bot.connect_by_id("664-591") #Put your 6-digit sensor ID here
    
    for _ in range(100):
        distance = bot.read_data("Distance")
        if distance != 0:
            print(distance)
            bot.drive((distance-target_distance)/10, 1)
        time.sleep(0.1)
    bot.reset()
    bot.disconnect()

if __name__ == "__main__":
    maintain(100)