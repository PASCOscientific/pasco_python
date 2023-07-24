from src.pasco.pasco_bot import PascoBot
from src.pasco.pasco_ble_device import PASCOBLEDevice
import time

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

def lift_and_turn():
    # line up gary's arm
    release()
    lift()
    for i in range(5):
        # make gary turn until he sees the box
        gary.turn_continuous(120)
        distance = gary.read_data('Distance')
        while distance > 100 or distance < 10:
            distance = gary.read_data('Distance')

        print(f"Distance: {gary.read_data('Distance')}")
        gary.stop_steppers(360, 360)
        gary.turn(-50, 180)

        lower()
        grab()
        lift()

        gary.turn(180, 360)
        release()

    gary.turn(-180, 360)

if __name__ == "__main__":
    gary = PascoBot()
    gary.connect_by_id('664-591')

    larry = PASCOBLEDevice()
    larry.connect_by_id('363-480')
    lift()
    release()
    gary.drive(10, 10)
    while gary.read_data('Distance')>100:
        print(f"Distance: {gary.read_data('Distance')}")
    gary.stop_steppers(360, 360)
    lower()
    grab()
    lift()

    initial_SolarPAR = larry.read_data('SolarPAR')
    gary.drive(-5, 10)
    while(larry.read_data('SolarPAR') == initial_SolarPAR):
        print(f"SolarPAR: {larry.read_data('SolarPAR'):.2f}")
    gary.stop_steppers(360, 360)
    gary.turn(-180)
    release()

    larry.disconnect()
    gary.reset()
    gary.disconnect()