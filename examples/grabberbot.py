# grabberbot.py
from pasco import PascoBot, PASCOBLEDevice
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
    pasco_bot.set_servo(1, 'standard', -60)
    time.sleep(0.5)

def grab():
    while pasco_bot.read_data('ServoCurrentOrd', 1) < 20:
        pasco_bot.set_servo(1, 'standard', 20)

def lower():
    pasco_bot.set_servo(2, 'standard', 80)
    time.sleep(0.5)

def lift():
    pasco_bot.set_servo(2, 'standard', -60)
    time.sleep(0.5)

def grabberbot():
    lift()
    release()
    pasco_bot.drive(10, 10)
    distance = pasco_bot.read_data('Distance')
    while distance > 100:
        distance = pasco_bot.read_data('Distance')
        print(f"Distance: {distance}")

    pasco_bot.stop_steppers(360, 360)
    lower()
    grab()
    lift()
    pasco_bot.drive(-5, 10)
    time.sleep(0.5)
    force = force_sensor.read_data('Force')
    while force_sensor.read_data('Force') > FORCE_OFF_TABLE:
        force = force_sensor.read_data('Force')
        print(f"force: {force:.2f}")
    pasco_bot.stop_steppers(360, 360)
    pasco_bot.turn(-180)
    release()
    pasco_bot.turn(180)

def test_force():
    pasco_bot.drive(-5, 10)
    time.sleep(0.2)
    while force_sensor.read_data('Force') > 12.7:
        print(force_sensor.read_data('Force'))
    pasco_bot.stop_steppers(360, 360)
    pasco_bot.turn(180)

if __name__ == "__main__":
    pasco_bot = PascoBot()
    force_sensor = PASCOBLEDevice()
    try:
        botID = '123-456' # Put your 6-digit sensor ID here
        pasco_bot.connect_by_id(botID)
    except Exception as e:
        print(f"Could not connect to sensor: {botID}")
        print(type(e))
        exit()
    try:
        forceSensorID = '123-456' # Put your 6-digit sensor ID here
        force_sensor.connect_by_id(forceSensorID)
    except Exception as e:
        if pasco_bot.is_connected():
            pasco_bot.disconnect()
        print(f"Could not connect to sensor: {forceSensorID}")
        print(type(e))
        exit()

    grabberbot()

    force_sensor.disconnect()
    pasco_bot.disconnect()