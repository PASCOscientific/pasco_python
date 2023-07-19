from src.pasco.control_node_device import ControlNodeDevice
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

def turn(angle, velocity=180):
    scale = 6.1/3.7
    sign = int(angle/abs(angle))
    gary.rotate_steppers_through(sign*velocity*scale, sign*360, scale*angle, sign*velocity*scale, sign*360, scale*angle, True)

def turn_continuous(angular_velocity):
    scaled_av = angular_velocity * 6.1/3.7
    gary.rotate_steppers_continuously(scaled_av, scaled_av/2, scaled_av, scaled_av/2)

if __name__ == "__main__":
    gary = ControlNodeDevice()
    gary.connect_by_id('664-591')

    # line up gary's arm
    release()
    lift()
    for i in range(5):
        # make gary turn until he sees the box
        turn_continuous(120)
        distance = gary.read_data('Distance')
        while distance > 100 or distance < 10:
            distance = gary.read_data('Distance')

        print(f"Distance: {gary.read_data('Distance')}")
        gary.stop_steppers(360, 360)
        turn(-50, 180)

        lower()
        grab()
        lift()

        turn(180, 360)
        release()

    turn(-180, 360)
    gary.reset()
    gary.disconnect()