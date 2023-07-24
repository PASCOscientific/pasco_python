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
    
    def turn(self, angle, velocity=180):
        scale = 6.1/3.7
        sign = int(angle/abs(angle))
        self.rotate_steppers_through(sign*velocity*scale, sign*360, scale*angle, sign*velocity*scale, sign*360, scale*angle, True)

    def turn_continuous(self, angular_velocity):
        scaled_av = angular_velocity * 6.1/3.7
        self.rotate_steppers_continuously(scaled_av, scaled_av/2, scaled_av, scaled_av/2)