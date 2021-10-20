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


    def set_leds_in_array(self, xy_list=[], intensity=128):
        """
        Set multiple LEDs on the 5x5 Matrix

        Args:
            xy_list (List): [[x0,y0]... [x4,y4]] A list of coordinate pairs, ex: [[4,4], [0,4], [2,2]]
                ---------------------------
                | 0,0  1,0  2,0  3,0  4,0 |
                | 0,1  1,1  2,1  3,1  4,1 |
                | 0,2  1,2  2,2  3,2  4,2 |
                | 0,3  1,3  2,3  3,3  4,3 |
                | 0,4  1,4  2,4  3,4  4,4 |
                ---------------------------
            intensity (int): [0-255] brightness control of LEDs in the array
        """
        if self.is_connected() is False:
            raise self.DeviceNotConnected()

        if intensity and type(intensity) not in (int, float):
            raise self.InvalidParameter

        led_activate = 0
        for x,y in xy_list:
            if (x and type(x) is not int) or (y and type(y) is not int):
                raise self.InvalidParameter
            if (x < 0 or x > 4) or (y < 0  or y > 4):
                raise self.InvalidParameter
            led_index = 20 - (y * 5) + x # Converts xy position to LED index
            led_activate += 2 ** led_index

        led_intensity = self._limit(intensity, 0, 255)

        cmd = [ self.GCMD_CODENODE_CMD, self.CODENODE_CMD_SET_LEDS,
                led_activate & 0xFF, led_activate>>8 & 0XFF, led_activate>>16 & 0XFF, led_activate>>24 & 0XFF,
                led_intensity ]
        self._send_command(self.SENSOR_SERVICE_ID, cmd)
        self._loop.run_until_complete(self._single_listen(self.SENSOR_SERVICE_ID))


    def set_rgb_led(self, red, green, blue):
        """
        Set the //code.Node's RGB LED
        
        Args:
            red (int): [0-255] brightness control of Red LED
            green (int): [0-255] brightness control of Green LED
            blue (int): [0-255] brightness control of Blue LED
        """
        if self.is_connected() is False:
            raise self.DeviceNotConnected()

        if ((red and type(red) not in (int, float)) or
            (green and type(green) not in (int, float)) or
            (blue and type(blue) not in (int, float))):
            raise self.InvalidParameter

        led_r = self._limit(red, 0, 255)
        led_g = self._limit(green, 0, 255)
        led_b = self._limit(blue, 0, 255)

        cmd = [ self.GCMD_CODENODE_CMD, self.CODENODE_CMD_SET_LEDS, led_r, led_g, led_b, 0X80, 0X00 ]
        self._send_command(self.SENSOR_SERVICE_ID, cmd)
        self._loop.run_until_complete(self._single_listen(self.SENSOR_SERVICE_ID))


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


    def scroll_text_in_array(self, text):
        """
        Scroll text/numbers on the 5x5 LED Array

        Args:
            text (str, float, int)
        """
        if self.is_connected() is False:
            raise self.DeviceNotConnected()

        if text and type(text) not in (int, float, str):
            raise self.InvalidParameter
        
        text = str(text)

        matrix = get_word(text.upper()) # Only uppercase characters for now
        for disp in matrix:
            self.set_leds_in_array(disp, 128)


    def show_image_in_array(self, icon_image):
        """
        Show an image from the preassembled library on the 5x5 LED Array
        
        Example: device.show_image_in_array(Icons().smile)

        Args:
            icon_image (Icon) - refer to the character_image library for a list.
        """
        if self.is_connected() is False:
            raise self.DeviceNotConnected()

        if icon_image and type(icon_image) is not dict:
            raise self.InvalidParameter

        try:
            matrix = get_icon(icon_image)
        except:
            raise self.InvalidParameter

        self.set_leds_in_array(matrix, 128)


    def reset(self):
        """
        Reset the speaker and LEDs on the code node
        """
        if self.is_connected() is False:
            raise self.DeviceNotConnected()

        self.set_rgb_led(0,0,0)
        self.set_leds_in_array([], 0)
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
