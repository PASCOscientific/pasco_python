from . import PASCOBLEDevice


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


    def set_sound_frequency(self, frequency):
        """
        Control the code node's built in speaker output frequency

        Args:
            Frequency (in hertz)
        """
        if self.is_connected() is False:
            raise self.DeviceNotConnected()

        if frequency and type(frequency) not in (int, float):
            raise self.InvalidParameter

        frequency = self._limit(frequency, 0, 20000)

        cmd = [ self.GCMD_CODENODE_CMD, self.CODENODE_CMD_SET_SOUND_FREQ, frequency & 0xFF, frequency>>8 & 0XFF ]
        self._send_command(self.SENSOR_SERVICE_ID, cmd)
        self._loop.run_until_complete(self._single_listen(self.SENSOR_SERVICE_ID))


    def reset(self):
        """
        Reset the speaker and LEDs on the code node
        """
        if self.is_connected() is False:
            raise self.DeviceNotConnected()

        self.set_sound_frequency(0)


def main():
    
    device = ControlNodeDevice()

    found_devices = device.scan()

    if len(found_devices) == 0:
        print("No devices found")
        exit(1)

    print('Devices Found')
    for i, ble_device in enumerate(found_devices):
        #print(ble_device.address)
        print(f'{i}: {ble_device.name}')

    # Auto connect if only one sensor found
    selected_device = input('Select a device: ') if len(found_devices) > 1 else 0
    ble_device = found_devices[int(selected_device)]
    device.connect(ble_device)


if __name__ == "__main__":
    main()
