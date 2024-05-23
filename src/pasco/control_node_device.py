from .pasco_ble_device import PASCOBLEDevice
import time
from struct import unpack, pack
from math import pi


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


    STEPS_PER_REV = 960
    DEGREES_PER_REV = 360
    DECISTEPS_PER_STEP = 10
    
    LSB_PWM_PERIOD = 0xd0                   # Least Significant Byte for Pulse Width Modulation period
    MSB_PWM_PERIOD = 0x07                   # Most Significant Byte for Pulse Width Modulation period

    CN_ACC_ID_NONE = 0
    CN_ACC_ID_MOTOR_BASE = 2500
    CN_ACC_ID_STEPPER_480 = 2501
    CN_ACC_ID_LOW_SPEED_STEPPER= 2502
    CN_ACC_ID_MOTOR_3 = 2503
    CN_ACC_ID_LINE_FOLLOWER = 2504
    CN_ACC_ID_RANGE_SENSOR = 2505

    STEPPER_A_CHANNEL = 1
    STEPPER_B_CHANNEL = 2
    BOTH_STEPPER_CHANNEL = 3

    PLUGIN_CHANNELS = {'A': 0, 'B': 1, 'sensor': 2, 1: 3, 2: 3}
    # the 1: 3, 2: 3 are for the servo plugin locations. 
    # they get their response data on the onboard sensor channel.


# ----------- Reading Data --------------

    def read_data(self, measurement: str, port=None):
        """
        Read a sensor measurement

            measurement (string): name of measurement we want to read
            port (string | int) (optional): port of sensor from which we want the measurement
        """
        if self.is_connected() is False:
            raise self.DeviceNotConnected()

        if measurement == None or type(measurement) is not str:
            raise self.InvalidParameter
        else:
            if port == None:
                return super().read_data(measurement)
                
            elif type(port) == str:
                # If the port is A or B, then we are sensing two steppers. 
                # Interpret the plugin channel to query the correct sensor, and convert from radians to degrees.
                sensor_id = self.PLUGIN_CHANNELS[port]
                self._get_sensor_measurements(sensor_id)
                measurement_id = None
                for m_id, m in self._device_measurements[sensor_id].items():
                    if m['NameTag'] == measurement:
                        measurement_id = m_id
                measure = self._sensor_data[sensor_id][measurement_id]
                if measurement in ["Angle", "AngularVelocity"]:
                    measure = round(measure * 180/pi, 1)
                return measure
            
            if type(port) == int:
                # If we're getting a response for a servo resistance, query the onboard sensor
                # Because we are interpreting the data manually we need to query manually.
                self._request_sensor_data(sensor_id=self.PLUGIN_CHANNELS[port])
                onboard_sensor_data = list(unpack('<hhhbb', self._data_packet))
                # the data for the servo resistance is indices 3 and 4 of the response
                return onboard_sensor_data[port+2]*12.5
        
        return self.MeasurementNotFound
    


# ----------- Steppers --------------

    def _get_stepper_remaining(self):
        """
        INTERNAL
        Get info on the steppers for rotate_steppers_through command
        returns degree_info (list[float]): list of information about remaining tasks for stepper.

        degree_info[0] = degrees remaining for port A stepper

        degree_info[1] = degrees remaining for port B stepper

        degree_info[2] = acceleration (deg/s/s) remaining for port A stepper

        degree_info[3] = acceleration (deg/s/s) remaining for port B stepper
        """
        service = 0
        size = 2
        command = [self.GCMD_CONTROL_NODE_CMD, self.CTRLNODE_CMD_DETECT_DEVICES, size]
        self._loop.run_until_complete(self.write_await_callback(service, command))
        """
        self._response_data looks like so:
        - 192  \
        - 0     } generic response data
        - 55   /
        - steps remaining for port A bit 1
        - steps remaining for port A bit 2
        - steps remaining for port B bit 1
        - steps remaining for port B bit 2
        - acceleration remaining for port A bit 1
        - acceleration remaining for port A bit 2
        - acceleration remaining for port B bit 1
        - acceleration remaining for port B bit 2
        - steps remaining for port A extra bit
        - steps remaining for port B extra bit
        """
        raw_stepper_info = list(unpack('<hhhhbb', self._data_packet))
        # add in the extra bits for steps remaining
        raw_stepper_info[0] += raw_stepper_info[4] << 8
        raw_stepper_info[1] += raw_stepper_info[5] << 8
        raw_stepper_info = raw_stepper_info[0:4]
        degree_info = [data/self.STEPS_PER_REV * self.DEGREES_PER_REV for data in raw_stepper_info]
        return degree_info

    def _send_stepper_command(self, speedA, accelerationA, distanceA, speedB, accelerationB, distanceB):
        """
        INTERNAL
        Args:
            speed: degrees/second
            acceleration: degrees/second/second
            distance: degrees or 'continous'

        If distance == 'continous' then the steppers rotate continuously
        To send a command to only one stepper, set the other stepper's parameters to None.
        i.e. if accelerationA is None then only stepper B will run.

        """

        # determine what steppers we are sending commands to
        stepper_channel = self.BOTH_STEPPER_CHANNEL
        if accelerationA == None and accelerationB != None:
            stepper_channel = self.STEPPER_B_CHANNEL
            accelerationA = 0
            speedA = 0
            distanceA = 0
        if accelerationB == None and accelerationA != None: 
            stepper_channel = self.STEPPER_A_CHANNEL
            accelerationB = 0
            speedB = 0
            distanceB = 0

        # deal with rotating stepper continuously
        continous1 = distanceA == 'continuous'
        continous2 = distanceB == 'continuous'
        
        # this scales up the command to account for the low speed stepper's gearing
        mul = {}
        for sensor in self._device_channels:
            if 'channel_id_tag' in sensor:
                mul[sensor['id']] = 6 if sensor['sensor_id'] == self.CN_ACC_ID_LOW_SPEED_STEPPER else 1

        # Convert speeds from deg/s[/s] to decisteps/s[/s] and distances from deg to steps
        
        speedA = speedA * mul[0] * self.DECISTEPS_PER_STEP * self.STEPS_PER_REV / self.DEGREES_PER_REV
        speedB = speedB * mul[1] * self.DECISTEPS_PER_STEP * self.STEPS_PER_REV / self.DEGREES_PER_REV
        accelerationA = accelerationA * mul[0] * self.DECISTEPS_PER_STEP * self.STEPS_PER_REV / self.DEGREES_PER_REV
        accelerationB = accelerationB * mul[1] * self.DECISTEPS_PER_STEP * self.STEPS_PER_REV / self.DEGREES_PER_REV
        distanceA = 0 if continous1 else abs(distanceA) * mul[0] * self.STEPS_PER_REV / self.DEGREES_PER_REV
        distanceB = 0 if continous2 else abs(distanceB) * mul[1] * self.STEPS_PER_REV / self.DEGREES_PER_REV
        # we have to take abs() of the distances because if the 
        # user enters a negative distance the stepper will rotate infinitely

        speedA = int(self._limit( speedA, -19200, 19200 ))
        accelerationA = int(self._limit( accelerationA, 0, 65535 ))
        distanceA = int(self._limit( distanceA, 0, 65535 ))
        speedB = int(self._limit( speedB, -19200, 19200 ))
        accelerationB = int(self._limit( accelerationB, 0, 65535 ))
        distanceB = int(self._limit( distanceB, 0, 65535 ))

        """
        Stepper command has 16 bits:
        - command "set stepper"
        - channels (1, 2, 3 <-> port A, B, both)
        - 2 bits target speed channel 1
        - 2 bits acceleration channel 1
        - 2 bits distance channel 1
        - 2 bits target speed channel 2
        - 2 bits acceleration channel 2
        - 2 bits distance channel 2
        - extra bit distance channel 1
        - extra bit distance channel 2
        """

        command = [ self.GCMD_CONTROL_NODE_CMD, self.CTRLNODE_CMD_SET_STEPPER, stepper_channel, 
            speedA & 0xFF, speedA>>8 & 0XFF,
            accelerationA & 0xFF, accelerationA>>8 & 0XFF,
            distanceA & 0xFF, distanceA>>8 & 0XFF,
            speedB & 0xFF, speedB>>8 & 0XFF,
            accelerationB & 0xFF, accelerationB>>8 & 0XFF,
            distanceB & 0xFF, distanceB>>8 & 0XFF
        ]

        self._loop.run_until_complete(self.write_await_callback(self.SENSOR_SERVICE_ID, command))


    def rotate_steppers_continuously(self, speedA, accelerationA, speedB, accelerationB):
        """
        rotate steppers continuously at given accelerations to given velocities
        Args:
            speedA (float):        target velocity for stepper plugged into port A
            accelerationA (float): acceleration to reach target velocity for stepper A
            speedB (float):        target velocity for stepper plugged into port B
            accelerationA (float): acceleration to reach target velocity for stepper B

        """
        if not self.is_connected():
            raise self.DeviceNotConnected()
        
        self._send_stepper_command(
            speedA, accelerationA, 'continuous', speedB, accelerationB, 'continuous')


    def rotate_stepper_continuously(self, port, speed, acceleration):
        """
        Rotate a single stepper continously
        Args:
            port (str): port of stepper
            speed (double): target velocity for stepper
            acceleration (double): acceleration to reach target velocity
        """
        if port.upper() == "A":
            self.rotate_steppers_continuously(speed, acceleration, None, None)
        elif port.upper() == "B":
            self.rotate_steppers_continuously(None, None, speed, acceleration)    
        else:
            raise self.InvalidParameter()


    def stop_steppers(self, accelerationA, accelerationB):
        """
        Decelarate steppers at given accelerations until they stop
        Args:
            accelerationA (double): acceleration at which to stop stepper A
            accelerationB (double): acceleration at which to stop stepper B

        """
        self._send_stepper_command(
            0, accelerationA, 'continuous', 0, accelerationB, 'continuous')
        

    def stop_stepper(self, port, acceleration):
        """
        Stop the stepper in the given port with given acceleration

        Args:
            port (str): port of stepper
            acceleration (float): acceleration to stop at
        """
        if port.upper() == "A":
            self.stop_steppers(acceleration, None)
        elif port.upper() == "B":
            self.stop_steppers(None, acceleration)  
        else:
            raise self.InvalidParameter()
        pass


    def rotate_steppers_through(self, speedA, accelerationA, distanceA, speedB, accelerationB, distanceB, await_completion=False):
        """
        Rotate the steppers through the given distances

        Args:
            speedA (float):          target velocity for stepper plugged into port A (deg/s)
            accelerationA (float):   acceleration to reach target velocity for stepper A (deg/s/s)
            distanceA (float):       distance to run stepper A (deg)
            speedB (float):          target velocity for stepper plugged into port B (deg/s)
            accelerationB (float):   acceleration to reach target velocity for stepper B (deg/s/s)
            distanceB (float):       distance to run stepper B (deg)
            await_completion (bool): whether to stop execution to wait for the stepper to finish rotating

        """
        if self.is_connected() is False:
            raise self.DeviceNotConnected()

        self._send_stepper_command(
            speedA, accelerationA, distanceA, speedB, accelerationB, distanceB
        )

        if await_completion:
            degrees_remaining = self._get_stepper_remaining()
            while degrees_remaining[0] > 0 or degrees_remaining[1] > 0:
                degrees_remaining = self._get_stepper_remaining()
        


    def rotate_stepper_through(self, port, speed, acceleration, distance, await_completion=False):
        """
        Rotate a single stepper through the given distance
        Args:
            port (str):              port stepper is plugged into
            speed (float):           target velocity for stepper plugged into port (deg/s)
            acceleration (float):    acceleration to reach target velocity for stepper (deg/s/s)
            distance (float):        distance to run stepper (deg)
            await_completion (bool): whether to stop execution to wait for the stepper to finish rotating
        """
        if port.upper() == "A":
            self.rotate_steppers_through(speed, acceleration, distance, None, None, None, await_completion)
        elif port.upper() == "B":
            self.rotate_steppers_through(None, None, None, speed, acceleration, distance, await_completion) 
        else:
            raise self.InvalidParameter()


# -------------- Servos ----------------

    def _calculate_on_time(self, measure_type, value):
        """
        INTERNAL
        Args:
            measure_type (str): type of servo measure. "standard" or "continuous"
            value (float):      value of measure to set servos to
        Calculate the on-time of the PWM command.
        Servos are controlled by Pulse Width Manipulation: commands are sent via 20 ms
        pulses, where the width of the pulse corresponds to the value of the command.
        The formula of the relation depends on the command:
        - angle:   t = (angle + 150) [10 microseconds]
        - % speed: t = 0.2p   + 150  [10 microseconds] (where p is a percent of the total speed)
        The control Node interprets the data in units of 10 microseconds = 100 ms.
        """
        on_time = 0
        if measure_type == "standard":
            on_time = int(value + 150)
        elif measure_type == "continuous":
            on_time = int(0.2*value + 150)

        return on_time

    def set_servos(self, ch_1_type, ch_1_value, ch_2_type, ch_2_value):
        """
        set the servos in channels 1 and 2
        Args:
            ch_1_type (str): "standard" or "continuous" servo type
            ch_1_value (float): value of either degrees or percent speed
            ch_2_type (str): "standard" or "continuous" servo type
            ch_2_value (float): value of either degrees or percent speed
        """
        if not self.is_connected:
            raise self.DeviceNotConnected()
        
        if self.is_connected() is False:
            raise self.DeviceNotConnected()

        # determine what servo channels you are powering:
        # 1: channel 1 only
        # 2: channel 2 only
        # 3: channel 1 and channel 2
        channels = int(ch_1_type != 0) + 2*int(ch_2_type != 0)
        # set_servos(0, 0, 0, 0) means ALL OFF and needs to go to both channels
        channels = 3 if channels == 0 else channels
        
        period1 = 2000 # 20 ms period (servo value)
        period2 = 2000 # 20 ms period (servo value)
        onTime1 = self._calculate_on_time(ch_1_type, ch_1_value)
        onTime2 = self._calculate_on_time(ch_2_type, ch_2_value)

        cmd = [ self.GCMD_CONTROL_NODE_CMD, self.CTRLNODE_CMD_SET_SERVO, channels, 
            onTime1 & 0xFF, onTime1>>8 & 0XFF,
            period1 & 0xFF, period1>>8 & 0XFF,
            onTime2 & 0xFF, onTime2>>8 & 0XFF,
            period2 & 0xFF, period2>>8 & 0XFF,
        ]
        self._loop.run_until_complete(self.write_await_callback(self.SENSOR_SERVICE_ID, cmd))

    def set_servo(self, port, type, value):
        """
        set a single servo
        Args:
            port (int): which servo channel to power (1 or 2)
            type (str): servo type. "standard" or "continuous".
            value (float): value of either degrees or percent speed
        """
        if port == 1:
            self.set_servos(type, value, 0, 0)
        elif port == 2:
            self.set_servos(0, 0, type, value)
        else:
            raise self.InvalidParameter()


# --------- Power Board ----------------

    def set_power_out(self, port: str, channel: int, output_type: str, value):
        """
        Control the power output board

        Args:
            port (str): Power Out port
            channel (int): Channel of the power output board
            output_type (either 'USB' or 'terminal'): output location
            value (0|1 for USB output or % for terminal): ON/OFF or % power

        The request message is as follows:
        - 0x05: we're talking to power out ports A and B
        - whichPins: encode which pins we want to control
        - LSB of PWM period (0xD0) <- we don't mess with these
        - MSB of PWM period (07)   <- we don't mess with these
        - A0 value // On (255), Off (0), or Duty cycle (1 to 254) for PWM on output A0
        - A1 value // On (255), Off (0), or Duty cycle (1 to 254) for PWM on output A1
        - A2 value // On (255), Off (0), or Duty cycle (1 to 254) for PWM on output A2
        - A3 value // On (255), Off (0), or Duty cycle (1 to 254) for PWM on output A3
        - B0 value // On (255), Off (0), or Duty cycle (1 to 254) for PWM on output B0
        - B1 value // On (255), Off (0), or Duty cycle (1 to 254) for PWM on output B1
        - B2 value // On (255), Off (0), or Duty cycle (1 to 254) for PWM on output B2
        - B3 value // On (255), Off (0), or Duty cycle (1 to 254) for PWM on output B3

        The Power Out ports A and B have four wires each that control the power out board:
        A0,A1 A2,A3
        -CH1- -CH2-  
        Each of these can be set to 0V, +5V, or a PWM
        The combination of port and channel is used to determine the wires (aka pins) we are controlling.
        Our set of pins we want to control is encoded as a single number corresponding to a binary 
        representation of the pins:
        __ __ __ __ __ __ __ __
        B3 B2 B1 B0 A3 A2 A1 A0
        Controlling A1 and A0 (port A channel 1) would be indicated by sending 11 in binary (3)
        Controlling B3 and B2 (port B channel 2) would be indicated by sending 11000000 in binary (192)

        The values of our pins control the power going to them:
            A0: USB Vbus pin and terminal pin labeled '+' for channel 1
            A1: USB Vbus gnd and unlabeled terminal pin for channel 1
            A2: USB Vbus pin and terminal pin labeled '+' for channel 2
            A3: USB Vbus gnd and unlabeled terminal pin for channel 2

        """
        # 1. Where are we talking?
        # port and channel are used to figure out which_pins
        # A CH1 -> 11       -> 3
        # A CH2 -> 1100     -> 12
        # B CH1 -> 110000   -> 48
        # B CH2 -> 11000000 -> 192

        encode_which_pins = {
            ('A', 1): 3,
            ('A', 2): 12,
            ('B', 1): 48,
            ('B', 2): 192,
            }
        which_pins = encode_which_pins[(port.upper(), channel)]

        first_pin_indices = {
            ('A', 1): 0,
            ('A', 2): 2,
            ('B', 1): 4,
            ('B', 2): 6,
            }
        first_pin_index = first_pin_indices[(port.upper(), channel)]

        # 2. What are we talking to? USB or terminal?
        lsb_pwm_period = self.LSB_PWM_PERIOD if output_type == 'terminal' else 0x00
        msb_pwm_period = self.MSB_PWM_PERIOD if output_type == 'terminal' else 0x00
        # these values will be what we end up sending
        values = [0, 0, 0, 0, 0, 0, 0, 0]

        if output_type.upper() == 'USB':
            values[first_pin_index] = 255 if int(value) > 0 else 0
        
        if output_type.lower() == 'terminal':
            # convert a percentage (0-100) to a duty cycle value (1-254)
            duty_cycle = int(2.53*abs(value) + 1)
            # If the power percent is positive we want to rotate forward
            # so we send the signal to the first of the control pins for the channel.
            # If it's negative we want to rotate backward 
            # so we send the signal to the second of the control pins for the channel
            i = first_pin_index if value >= 0 else first_pin_index + 1
            values[i] = duty_cycle

        
        cmd = [ self.GCMD_CONTROL_NODE_CMD, self.CTRLNODE_CMD_SET_SIGNALS, which_pins, 
            lsb_pwm_period, msb_pwm_period
        ]
        cmd.extend(values)
        self._loop.run_until_complete(self.write_await_callback(self.SENSOR_SERVICE_ID, cmd))


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
        self._loop.run_until_complete(self.write_await_callback(self.SENSOR_SERVICE_ID, cmd))

    # ----------- Greenhouse light -----------------

    def set_greenhouse_light(self, port: str, Red: float, Blue: float) -> None:
        """
        control the greenhouse light
        args:
            port (str): either A or B. Port of the control node to which the greenhouse light is attached
            R (float): percent power of red light
            B (float): percent power of blue light

        The message encoding is as follows:
        - which_pins (either [A0, A2] or [B0, B2] depending on the port selected)
          These are encoded: 0x05        0x50 (see comment for power output board)
        - PWM value of Red  (0-255)
        - PWM value of Blue (0-255)
        """
        which_pins = {'A':0x0F, 'B':0xF0}
        # scale up from 0-100 (percent) to 255-0
        # because the brightness is inverted. +5V from the control node turns off the light.
        Red_value = int((100-Red) * 2.55) + 1
        Blue_value = int((100-Blue) * 2.55) + 1
        # As described in the power output board docstring, the last 8 bytes of the command
        # are the values for ports A and B: 4 for A, then 4 for B
        if port.upper() == 'A':
            values = [Red_value, 0, Blue_value, 0] 
        elif port.upper() == 'B':
            values = [0, 0, 0, 0, Red_value, 0, Blue_value, 0]
        else:
            raise self.InvalidParameter
        
        cmd = [self.GCMD_CONTROL_NODE_CMD, self.CTRLNODE_CMD_SET_SIGNALS, which_pins[port.upper()], self.LSB_PWM_PERIOD, self.MSB_PWM_PERIOD]
        cmd.extend(values)
        self._loop.run_until_complete(self.write_await_callback(self.SENSOR_SERVICE_ID, cmd))


# --------- Convenience -----------

    def reset(self):
        """
        Turn off all accessories on the control node
        We do this by sending a single stop accessories byte
        """
        
        if self.is_connected() is False:
            raise self.DeviceNotConnected()
        
        else:
            cmd = [self.GCMD_CONTROL_NODE_CMD, self.CTRLNODE_CMD_STOP_ACCESSORIES]
            self._loop.run_until_complete(self.write_await_callback(self.SENSOR_SERVICE_ID, cmd))
            
    def disconnect(self):
        """
        Extend the pasco_ble_device's disconnect to first reset all control node devices
        """
        self.reset()
        super().disconnect()

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
