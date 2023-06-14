# maintainRange.py
# Corbin Weiss
# created 2023-6-5

from src.pasco import PascoBot
import time
import math
"""
This program will make the PASCO bot maintain a given distance
from an object (e.g. your hand) by moving forward and backward
This won't work until we figure out how to read from the RangeFinder
"""


def maintain(target_distance):
    bot = PascoBot()
    bot.connect_by_id("651-400")
    
    for _ in range(100):
        distance = bot.read_data("Range")
        if distance != 0:
            print(distance)
            bot.drive((distance-target_distance)/10, 1)
        time.sleep(0.1)
    bot.reset()
    bot.disconnect()

if __name__ == "__main__":
    maintain(100)