import character_library

from code_node_device import CodeNodeDevice
from pasco_ble_device import PASCOBLEDevice


def main():
    # Connect to PASCO Device
    pCodeNode = CodeNodeDevice('//code.Node')
    pForce = PASCOBLEDevice('Force')

    pCodeNode.code_node_reset()
    light_on = False

    while True:
        if pForce.value_of('Force') > 10:
            if light_on == False:
                pCodeNode.code_node_set_rgb_leds(5,5,5)
                pCodeNode.code_node_set_sound_frequency(200)
                pCodeNode.show_image_in_array(character_library.Icons().smile)
                light_on = True
            else:
                pCodeNode.code_node_reset()
                light_on = False
            while pForce.value_of('Force') > 10:
                pass


if __name__ == "__main__":
    main()
