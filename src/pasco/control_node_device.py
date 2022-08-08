from .pasco_ble_device import PASCOBLEDevice
import time


class ControlNodeDevice(PASCOBLEDevice):
    # Control Node commands
    CTRLNODE_CMD_SET_SERVO = 3              # Enables PWM to servo
    CTRLNODE_CMD_SET_STEPPER = 4            # Enables stepper motor
    CTRLNODE_CMD_SET_SIGNALS = 5            # Sets motor control signals directly
    CTRLNODE_CMD_XFER_ACCESSORY = 6         # Write I2C accessory and read response
    CTRLNODE_CMD_READ_LINE_FOLLOWER = 7     # Read the line follower accessory
    CTRLNODE_CMD_GET_STEPPER_INFO = 8       # Get stepper remaining distance and remaining angular velocity to accelerate to
    CTRLNODE_CMD_STOP_ACCESSORIES = 9       # Turn off all steppers, servos, and accessories
    CTRLNODE_CMD_SET_BEEPER = 10            # Set beeper frequency

    CN_ACC_ID_NONE = 0
    CN_ACC_ID_MOTOR_BASE = 2500
    CN_ACC_ID_STEPPER_480 = 2501
    CN_ACC_ID_STEPPER_4800 = 2502
    CN_ACC_ID_MOTOR_3 = 2503
    CN_ACC_ID_LINE_FOLLOWER = 2504
    CN_ACC_ID_RANGE_SENSOR = 2505


    def set_steppers(self, speed1, accel1, distance1, speed2, accel2, distance2):
        """
        Set the Control Node stepper motors

        Args:
            speed1 (float): deg/s
            accel1 (float): deg/s/s
            distance1 (float): degrees
            speed2 (float): deg/s
            accel2 (float): deg/s/s
            distance2 (float): degrees
        """
        if self.is_connected() is False:
            raise self.DeviceNotConnected()

        mul = {}
        for sensor in self._setup_sensors:
            if 'channel_id_tag' in sensor:
                mul[sensor['id']] = 10 if sensor['sensor_id'] == self.CN_ACC_ID_STEPPER_4800 else 1

        # Convert speeds from deg/s[/s] to decisteps/s[/s] and distances from deg to steps
        STEPS_PER_REV = 960
        DEGREES_PER_REV = 360
        DECISTEPS_PER_STEP = 10
        
        speed1 = speed1 * mul[0] * DECISTEPS_PER_STEP * STEPS_PER_REV / DEGREES_PER_REV
        speed2 = speed2 * mul[1] * DECISTEPS_PER_STEP * STEPS_PER_REV / DEGREES_PER_REV
        accel1 = accel1 * mul[0] * DECISTEPS_PER_STEP * STEPS_PER_REV / DEGREES_PER_REV
        accel2 = accel2 * mul[1] * DECISTEPS_PER_STEP * STEPS_PER_REV / DEGREES_PER_REV
        distance1 = distance1 * mul[0] * STEPS_PER_REV / DEGREES_PER_REV
        distance2 = distance2 * mul[1] * STEPS_PER_REV / DEGREES_PER_REV

        speed1 = int(self._limit( speed1, -19200, 19200 ))
        accel1 = int(self._limit( accel1, 0, 65535 ))
        distance1 = int(self._limit( distance1, 0, 65535 ))
        speed2 = int(self._limit( speed2, -19200, 19200 ))
        accel2 = int(self._limit( accel2, 0, 65535 ))
        distance2 = int(self._limit( distance2, 0, 65535 ))

        cmd = [ self.GCMD_CONTROL_NODE_CMD, self.CTRLNODE_CMD_SET_STEPPER, 3, 
            speed1 & 0xFF, speed1>>8 & 0XFF,
            accel1 & 0xFF, accel1>>8 & 0XFF,
            distance1 & 0xFF, distance1>>8 & 0XFF,
            speed2 & 0xFF, speed2>>8 & 0XFF,
            accel2 & 0xFF, accel2>>8 & 0XFF,
            distance2 & 0xFF, distance2>>8 & 0XFF
        ]
        self._send_command(self.SENSOR_SERVICE_ID, cmd)


    def set_servos(self, ch_1_type, ch_1_angle, ch_2_type, ch_2_angle):
        """
        Control a servo motor

        Args:
            ch_1_type (int): 0 off, 1 standard servo, 2 continuous servo
            ch_1_angle (float): [-90:90] degrees for standard servo, [-100:100] speed for continuous servo

            ch_2_type (int): 0 off, 1 standard servo, 2 continuous servo
            ch_2_angle (float): [-90:90] degrees for standard servo, [-100:100] speed for continuous servo
        """

        # TODO: Test servo channel 2 with final Control Node

        if self.is_connected() is False:
            raise self.DeviceNotConnected()

        ch_1_value = 1 if ch_1_type > 0 else 0
        ch_2_value = 2 if ch_2_type > 0 else 0

        channels = ch_1_value + ch_2_value
        
        period1 = 2000 # 20 ms period (servo value)
        period2 = 2000 # 20 ms period (servo value)
        onTime1 = 0
        onTime2 = 0

        if ch_1_type == 1:
            # Standard Servo
            onTime1 = self._calc_4_params(ch_1_angle, -90, 60, 90, 240)
            onTime1 = int(self._limit(onTime1, 60, 240))
        elif ch_1_type == 2:
            #Continuous Servo
            onTime1 = self._calc_4_params(ch_1_angle, -100, 135, 100, 165)
            onTime1 = int(self._limit(onTime1, 135, 165))

        if ch_2_type == 1:
            # Standard Servo
            onTime2 = self._calc_4_params(ch_2_angle, -90, 60, 90, 240)
            onTime2 = int(self._limit(onTime2, 60, 240))
        elif ch_2_type == 2:
            #Continuous Servo
            onTime2 = self._calc_4_params(ch_2_angle, -100, 138, 100, 162)
            onTime2 = int(self._limit(onTime2, 135, 165))

        cmd = [ self.GCMD_CONTROL_NODE_CMD, self.CTRLNODE_CMD_SET_SERVO, channels, 
            onTime1 & 0xFF, onTime1>>8 & 0XFF,
            period1 & 0xFF, period1>>8 & 0XFF,
            onTime2 & 0xFF, onTime2>>8 & 0XFF,
            period2 & 0xFF, period2>>8 & 0XFF,
        ]
        self._send_command(self.SENSOR_SERVICE_ID, cmd)


    # TODO: Test this
    def set_power_out(self):
        """
        Control the power output board

        Args:
        """
        signalBits = 2
        pwmPeriod = 1000
        pwmValues = [10, 10, 10, 10, 10, 10, 10, 10]
        
        cmd = [ self.GCMD_CONTROL_NODE_CMD, self.CTRLNODE_CMD_SET_SIGNALS, signalBits, 
            pwmPeriod & 0xFF, pwmPeriod>>8 & 0XFF,
            pwmValues[0], pwmValues[1], pwmValues[2], pwmValues[3],
            pwmValues[4], pwmValues[5], pwmValues[6], pwmValues[7]
        ]
        self._send_command(self.SENSOR_SERVICE_ID, cmd)


    def set_sound_frequency(self, frequency):
        """
        Set the frequency of the control node's built in speaker

        Args:
            Frequency (in hertz)
        """
        if self.is_connected() is False:
            raise self.DeviceNotConnected()

        if frequency and type(frequency) not in (int, float):
            raise self.InvalidParameter

        frequency = self._limit(frequency, 0, 20000)

        cmd = [ self.GCMD_CONTROL_NODE_CMD, self.CTRLNODE_CMD_SET_BEEPER, frequency & 0xFF, frequency>>8 & 0XFF ]
        self._send_command(self.SENSOR_SERVICE_ID, cmd)


    def reset(self):
        """
        Reset the speaker and LEDs on the code node
        """
        if self.is_connected() is False:
            raise self.DeviceNotConnected()

        self.set_sound_frequency(0)
        self.set_servos(0, 0, 0, 0)
        self.set_steppers(0, 0, 0, 0, 0, 0)


def main():
    
    device = ControlNodeDevice()

    found_devices = device.scan()

    if len(found_devices) == 0:
        print("No devices found")
        exit(1)

    print('Devices Found')
    for i, ble_device in enumerate(found_devices):
        print(f'{i}: {ble_device.name}')

    selected_device = input('Select a device: ') if len(found_devices) > 1 else 0
    ble_device = found_devices[int(selected_device)]

    device.connect(ble_device)

    device.set_sound_frequency(500)

    """
    speed1 = 100
    accel1 = 0
    distance1 = 360
    speed2 = 100
    accel2 = 0
    distance2 = 360

    device.set_steppers(speed1, accel1, distance1, speed2, accel2, distance2)
    """

    
    for i in range(-100,101, 10):
        device.set_servos(2, i, 0, i)
        time.sleep(1)

    i = 0
    device.set_servos(1, i, 0, i)

    #device.controlnode_signals()

    device.disconnect()
    #for i in range(100):
    #    for m in measurements:
    #        print(f'{m} : {my_sensor.read_data(m)}')


if __name__ == "__main__":
    main()
