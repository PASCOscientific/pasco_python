import character_library
from pasco_py_beta import PASCOBLEDevice


class CodeNodeDevice(PASCOBLEDevice):
    GCMD_CODENODE_CMD = 0x37
    CODENODE_CMD_SET_LED = 0X02
    CODENODE_CMD_SET_LEDS = 0X03
    CODENODE_CMD_SET_SOUND_FREQ = 0X04


    def _led_0_to_255(self, intensity):
        """
        Convert intensity value to 0-255

        Args:
            intensity (int): [0-255] brightness of LED
        """
        if intensity <= 0:
            return 0
        elif intensity > 10:
            return 255



    def set_led_in_array(self, x, y, intensity=0):
        """
        Set an individual LED on the 5x5 matrix

        Args:
            x (int): [0-4] column value (top to bottom)
            y (int): [0-4] row value (left to right)
            intensity (int): [0-255] brightness control of LED
        """
        led_index = 20 - (y * 5) + x # Converts xy position to LED index
        led_intensity = self._led_0_to_255(intensity)

        cmd = [ self.GCMD_CODENODE_CMD, self.CODENODE_CMD_SET_LED, led_index, led_intensity ]
        self._send_command(0, cmd, True)
        self.loop.run_until_complete(self._single_listen(self.SENSOR_SERVICE_ID))


    def set_leds_in_array(self, led_array=[], intensity=0):
        """
        Set multiple LEDs on the 5x5 Matrix

        Args:
            led_array (List): [[x0,y0]... [x4,y4]] A list of coordinate pairs, ex: [[4,4], [0,4], [2,2]]
                ---------------------------
                | 0,0  1,0  2,0  3,0  4,0 |
                | 0,1  1,1  2,1  3,1  4,1 |
                | 0,2  1,2  2,2  3,2  4,2 |
                | 0,3  1,3  2,3  3,3  4,3 |
                | 0,4  1,4  2,4  3,4  4,4 |
                ---------------------------
            intensity (int): [0-255] brightness control of LEDs in the array
        """
        led_activate = 0
        for x,y in led_array:
            led_index = 20 - (y * 5) + x # Converts xy position to LED index
            led_activate += 2 ** led_index

        led_intensity = self._led_0_to_255(intensity)

        cmd = [ self.GCMD_CODENODE_CMD, self.CODENODE_CMD_SET_LEDS,
                led_activate & 0xFF, led_activate>>8 & 0XFF, led_activate>>16 & 0XFF, led_activate>>24 & 0XFF,
                led_intensity ]
        self._send_command(0, cmd)
        self.loop.run_until_complete(self._single_listen(self.SENSOR_SERVICE_ID))


    def set_rgb_led(self, r=0, g=0, b=0):
        """
        Set the //code.Node's RGB LED
        
        Args:
            0-255
            r (int): [0-10] brightness control of Red LED
            g (int): [0-10] brightness control of Green LED
            b (int): [0-10] brightness control of Blue LED
        """

        led_r = self._led_0_to_255(r)
        led_g = self._led_0_to_255(g)
        led_b = self._led_0_to_255(b)

        cmd = [ self.GCMD_CODENODE_CMD, self.CODENODE_CMD_SET_LEDS, led_r, led_g, led_b, 0X80, 0X00 ]
        self._send_command(0, cmd, True)
        self.loop.run_until_complete(self._single_listen(self.SENSOR_SERVICE_ID))


    def set_sound_frequency(self, frequency):
        """
        Control the code node's built in speaker output frequency

        Args:
            Frequency (in hertz)
        """
        cmd = [ self.GCMD_CODENODE_CMD, self.CODENODE_CMD_SET_SOUND_FREQ, frequency & 0xFF, frequency>>8 & 0XFF ]
        self._send_command(0, cmd, True)
        self.loop.run_until_complete(self._single_listen(self.SENSOR_SERVICE_ID))


    def scroll_text_in_array(self, text):
        matrix = character_library.get_word(text)
        #print(matrix)
        for disp in matrix:
            self.set_leds_in_array(disp, 128)


    def show_image_in_array(self, image):
        matrix = character_library.get_icon(image)
        #print(matrix)
        self.set_leds_in_array(matrix, 128)


    def reset(self):
        self.set_rgb_led(0,0,0)
        self.set_leds_in_array([], 0)
        self.set_sound_frequency(0)
