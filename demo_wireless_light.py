import character_library

from pasco_ble import PASCOBLEDevice


def main():
    # Connect to PASCO Device
    pCodeNode = PASCOBLEDevice('//code.Node','a')
    pForce = PASCOBLEDevice('Force','a')

    pCodeNode.code_node_reset()
    light_on = False

    while True:
        if pForce.value_of('Force') > 10:
            if light_on == False:
                pCodeNode.code_node_set_rgb_leds(5,5,5)
                pCodeNode.code_node_set_sound_frequency(200)
                pCodeNode.code_node_show_icon(character_library.Icons().alien)
                light_on = True
            else:
                pCodeNode.code_node_reset()
                light_on = False
            while pForce.value_of('Force') > 10:
                pass


if __name__ == "__main__":
    main()
