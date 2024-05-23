"""
//control.Node testing
Corbin Weiss
5/23/2023 Begun

Objectives:
Create and test functionality for all functions of the 
//control.Node defined in SPARKvue.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pasco.control_node_device import ControlNodeDevice
import time


# ------------ Acceleration sensor sample rate benchmark ------------

def test_read_data():
    print("Testing Read Data")
    start = time.monotonic()
    for i in range(100):
        print(controlNode.read_data("Accelerationx"))
    end = time.monotonic()
    print(f"{end-start} seconds elapsed")
    print(f"{100/(end-start)} Hz sample rate")


# ------------ Steppers -----------
def test_steppers_continuous():
    print("rotating both steppers continuously")
    controlNode.rotate_steppers_continuously(360, 360, -360, 360)
    time.sleep(1)
    print(f"""
    A is rotating at {controlNode.read_data('AngularVelocity', 'A')} rad/s
    B is rotating at {controlNode.read_data('AngularVelocity', 'B')} rad/s
    """)
    time.sleep(1)
    controlNode.stop_steppers(360, 360)

def test_steppers_through():
    print("""
    rotating both steppers through
    A: 180 degrees
    B: 360 degrees
          """)
    controlNode.read_data('Angle', 'A')
    controlNode.read_data('Angle', 'B')
    controlNode.rotate_steppers_through(360, 360, 180, 360, 360, 360, True)
    print(f"""
    A rotated {controlNode.read_data('Angle', 'A')} degrees
    B rotated {controlNode.read_data('Angle', 'B')} degrees
    """)

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
def test_power_board():
    controlNode.set_power_out('b', 1, 'terminal', 100)
    time.sleep(1)
    controlNode.set_power_out('b', 2, 'usb', 1)
    controlNode.set_power_out('a', 2, 'usb', 1)
    time.sleep(1)
    controlNode.set_power_out('b', 1, 'usb', 0)
    controlNode.set_power_out('b', 2, 'usb', 0)
    controlNode.set_power_out('a', 2, 'usb', 0)


# -------- Set Sound Frequency --------
def test_sound():
    controlNode.set_sound_frequency(440)
    time.sleep(1)
    controlNode.set_sound_frequency(0)
    time.sleep(1)


# ------- Servo current -----------
def test_servos_current():
    controlNode.set_servo(2, "standard", 20)
    for i in range(20):
        print(controlNode.read_data('ServoCurrentOrd', 2))
        time.sleep(0.1)
    controlNode.set_servos(0, 0, 0, 0)

# ------- Set greenhouse light -------
def test_greenhouse_light():
    # This will start with the light red and gradually transition through purple to blue.
    for value in range(0, 100, 10):
        print(value)
        controlNode.set_greenhouse_light('B', 100 - value, value)
        time.sleep(1)
    controlNode.set_greenhouse_light('B', 0, 0)


if __name__ == "__main__":
    controlNode = ControlNodeDevice()
    controlNode.connect_by_id('653-498') #Put your 6-digit sensor ID here
    measurement_list = controlNode.get_measurement_list()
    [print(f"{m}: {controlNode.read_data(m)}") for m in measurement_list]
    controlNode.disconnect()





