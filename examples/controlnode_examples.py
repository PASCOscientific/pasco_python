# controlnode_examples.py
"""
The control node supports:
- Steppers (connected in ports A and B)
- Servos   (connected in servo ports 1 and 2)
- Power output board    (connected in port A or B)
- Plugin sensors such as rangefinder and line follower (connected in Sensor port)
This python file shows examples of how to work with these
"""
from pasco import ControlNodeDevice
import time

def steppers(controlNode: ControlNodeDevice):
    """
    Run this with the pascobot
    Plug the right stepper into port A and the left stepper into port B and the bot will drive forward
    """
    controlNode.rotate_steppers_through(-360, -360, 360, 360, 360, 360, await_completion=True)

def distance(controlNode: ControlNodeDevice):
    """
    Run this with the pascobot
    Plug the right stepper into port A and the left servo into port B. 
    Plug the rangefinder attachment into the Sensor port.
    The bot will drive forward and the console display the distance to the nearest object
    """
    controlNode.rotate_steppers_continuously(-360, -360, 360, 360)
    print("distances:")
    for i in range(20):
        print(controlNode.read_data('Distance'))
    controlNode.stop_steppers(360, 360)

def servos(controlNode: ControlNodeDevice):
    """
    Run this with the pascobot with the bot gripper attachment
    Plug the right stepper into port A and the left servo into port B. 
    Plug the rear servo into port 2 and the front servo into port 1
    """
    controlNode.set_servo(1, 'standard', -50)
    time.sleep(0.5)    # The servos are fast, but they still need time to complete the commands you send them
    controlNode.set_servo(2, 'standard', -50)
    time.sleep(0.5)
    controlNode.set_servo(1, 'standard', 20)
    time.sleep(0.5)
    controlNode.set_servo(2, 'standard', 20)
    time.sleep(0.5)

# To see steppers, servos and the range finder working together, see grabberbot.py

def power_board(controlNode: ControlNodeDevice):
    """
    Plug in a power output board into port A of your control node,
    with an accessory in the USB output of channel 1 on the power output board
    """
    controlNode.set_power_out('A', 1, 'USB', True)
    time.sleep(1)

def greenhouse_light(controlNode: ControlNodeDevice):
    """
    Plug the greenhouse light into port B of the control node.
    This will start with the light red and gradually transition 
    through purple to blue, then turn off
    """
    for value in range(0, 100, 10):
        print(value)
        controlNode.set_greenhouse_light('B', 100 - value, value)
        time.sleep(1)
    controlNode.set_greenhouse_light('B', 0, 0)

def main():
    controlNode = ControlNodeDevice()
    try:
        sensorID = '123-456' # Put your 6-digit sensor ID here
        controlNode.connect_by_id(sensorID)
    except Exception as e:
        print(f"Could not connect to sensor: {sensorID}")
        print(type(e))
        exit()
    # To find what measurements are available, call get_measurement_list()
    print(controlNode.get_measurement_list())

    # Pick what you want to try here
    greenhouse_light(controlNode)

    controlNode.reset()
    controlNode.disconnect()

if __name__ == "__main__":
    main()