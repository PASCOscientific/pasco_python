"""
//control.Node testing
Corbin Weiss
5/23/2023 Begun
Testing sensing ability. Getting None for acceleration or raw data on position.
Meanwhile the //code.Node is working fine and //control.Node works great on SPARKvue.

Testing speakers: set_sound_frequency works great.
Testing servos: standard servos work.
Testing steppers: kind of works. They keep running exactly as long as the program is running.  

Objectives:
Create and test functionality for all functions of the 
//control.Node defined in SPARKvue.
- read value of sensor
    - inherited from pasco_ble_device
- speaker
    - set frequency
    - turn on/off
- zero sensor
- servo
    - port input, set angle or rotate at speed
- high speed stepper
    - units input
    - port
    - rotate type
    - max speed
    - acceleration

- low speed stepper

------------
Each block has dropdown options
many have numeric input options as well
"""

from src.pasco import ControlNodeDevice
import time
import asyncio


# ------------ Read Data ------------
# Do we eventually want to be able to read data while other processes are going?
# e.g. a line following program who reads light data while running steppers
# In that case we will need to rethink the data reading method
def test_read_data():
    print("Testing Read Data")
    start = time.monotonic()
    for i in range(100):
        print(controlNode.read_data("Accelerationx"))
    end = time.monotonic()
    print(f"{end-start} seconds elapsed")
    print(f"{100/(end-start)} Hz sample rate")


# ------------ Set Steppers -----------
def test_steppers_continous():
    print("rotating both steppers continuously")
    controlNode.rotate_steppers_continuously(360, 360, -360, 360)
    time.sleep(1)
    controlNode.stop_steppers(90, 360)
    time.sleep(1)

def test_steppers_through():
    print("rotating both steppers through")
    controlNode.rotate_steppers_through(360, 90, 720, 360, 90, 720, await_completion=True)
    controlNode.stop_steppers(360, 360)

def test_steppers_complex():
    print("rotating A stepper continuously")
    controlNode.rotate_stepper_continuously("A", 360, 360)
    print("rotating B stepper through")
    controlNode.rotate_stepper_through("B", 360, 360, 360)
    time.sleep(5)
    print("stopping stepper A")
    controlNode.stop_stepper("A", 90)
    time.sleep(3)



# ------------ Set Servos -------------
def test_servos():
    print("testing servos")
    controlNode.set_servo(2, "standard", -86.2)
    for i in range(3):
        controlNode.set_servos("continuous", 100, "standard", 0)
        time.sleep(1)
        controlNode.set_servos("continuous", -10, "standard", 90)
        time.sleep(1)
    controlNode.set_servos(0, 0, "standard", 0)
    time.sleep(1)
    print("done")
# ----------- Set Power out -----------



# -------- Set Sound Frequency --------
def test_sound():
    controlNode.set_sound_frequency(440)
    time.sleep(1)
    controlNode.set_sound_frequency(0)
    time.sleep(1)

# The following was based on a misunderstanding of how stepper angle readings work.
# -------- Stepper Sensors -----------
def test_stepper_sensor():
    controlNode.rotate_steppers_continuously(360, 360, -360, 360)
    start = time.monotonic()
    print(f"A      B")
    for i in range(10):
        print(f"{controlNode.read_data('Angle', 'A'):.2f} {controlNode.read_data('Angle', 'B'):.2f}")

    stop = time.monotonic()
    print(f"time elapsed: {stop-start} seconds")
    print(f"sample rate: {10/(stop-start)} Hz")
    time.sleep(1)
    controlNode.stop_steppers(360, 360)
    print("---stopped---")

    print(f"{controlNode.read_data('Angle', 'B'):.2f} {controlNode.read_data('Angle', 'A'):.2f}")
    

# -------- get_stepper_info -----------

if __name__ == "__main__":
    controlNode = ControlNodeDevice()
    controlNode.connect_by_id('651-400')
    # test_stepper_sensor()
    test_steppers_through()
    controlNode.reset()
    controlNode.disconnect()





