import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pasco.pasco_bot import PascoBot
from src.pasco.pasco_ble_device import PASCOBLEDevice
import time


"""
Run this with the pascobot with the bot gripper attachment
1. Plug the right stepper into port A and the left servo into port B.
2. Plug the rear servo into port 2 and the front servo into port 1
3. Tape a force sensor to the back of the bot, with the force hook supporting the rear of the bot
   a few millimeters off the ground. 
4. Get an initial reading of the force resting on the table and suspended off the edge
   (as it would be after the bot backs up to the edge)
5. Pick a value between those readings and set FORCE_OFF_TABLE to that value.
6. Line up the bot facing directly away from a table edge with a box directly in front of it.
7. Run the program. The bot will go up to the box, pick it up, back up to the edge of the table,
   turn around, and drop the box.
""" 

FORCE_OFF_TABLE = 12.7

def release():
    gary.set_servo(1, 'standard', -60)
    time.sleep(0.5)

def grab():
    while(gary.read_data('ServoCurrentOrd', 1) < 20):
        gary.set_servo(1, 'standard', 20)

def lower():
    gary.set_servo(2, 'standard', 80)
    time.sleep(0.5)

def lift():
    gary.set_servo(2, 'standard', -60)
    time.sleep(0.5)


def grabberbot():
    lift()
    release()
    gary.drive(10,10)
    distance = gary.read_data('Distance')
    while distance > 100:
        distance = gary.read_data('Distance')
        print(f"Distance: {distance}")

    gary.stop_steppers(360, 360)
    lower()
    grab()
    lift()
    gary.drive(-5, 10)
    time.sleep(0.5)
    force = frank.read_data('Force')
    while(frank.read_data('Force') > FORCE_OFF_TABLE):
        force = frank.read_data('Force')
        print(f"force: {force:.2f}")
    gary.stop_steppers(360,360)
    gary.turn(-180)
    release()
    gary.turn(180)


def test_force():
    gary.drive(-5,10)
    time.sleep(0.2)
    while(frank.read_data('Force')>12.7):
        print(frank.read_data('Force'))
    gary.stop_steppers(360, 360)
    gary.turn(180)


if __name__ == "__main__":

    gary = PascoBot()
    gary.connect_by_id('664-591') #Put your 6-digit sensor ID here

    # frank is a force sensor
    frank = PASCOBLEDevice()
    frank.connect_by_id('248-287')

    grabberbot()
    frank.disconnect()
    gary.disconnect()