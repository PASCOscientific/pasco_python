import character_library

from code_node_device import CodeNodeDevice
from pasco_ble_device import PASCOBLEDevice


def main():
    # Connect to PASCO Device
    pCodeNode = CodeNodeDevice()
    pCodeNode.connect_by_id('020-122')
    #pForce = PASCOBLEDevice('Force')

    pCodeNode.reset()
    light_on = False

    while True:
        if light_on == False:
            pCodeNode.set_rgb_led(100,100,100)
            #pCodeNode.set_sound_frequency(200)
            #pCodeNode.scroll_text_in_array("HELLO")
            pCodeNode.show_image_in_array(character_library.Icons().smile)
            pCodeNode.show_image_in_array(character_library.Icons().sad)
            light_on = True
        else:
            pCodeNode.reset()
            light_on = False


if __name__ == "__main__":
    main()
