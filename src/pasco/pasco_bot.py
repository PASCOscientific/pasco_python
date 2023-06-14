from .control_node_device import ControlNodeDevice
import math

class PascoBot(ControlNodeDevice):

    WHEEL_RADIUS= 3.7 # wheel diameter in cm
    def drive(self, speed, acceleration):
        """
        drive at a given speed (cm/second) achieved at a given velocity (cm/s/s)
        """
        deg_speed = speed * 360/(2*math.pi*self.WHEEL_RADIUS)
        deg_acceleration = acceleration * 360/(2*math.pi*self.WHEEL_RADIUS)
        self.rotate_steppers_continuously(
            -deg_speed, deg_acceleration, deg_speed, deg_acceleration
        )
    