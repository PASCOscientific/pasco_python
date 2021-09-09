from paspy.code_node_device import CodeNodeDevice
from paspy.pasco_ble_device import PASCOBLEDevice
from paspy.character_library import Icons


def main():
    # Connect to PASCO Device
    p_code_node = CodeNodeDevice()
    p_code_node.connect_by_id('020-122')

    #p_code_node.reset()
    light_on = False

    while True:
        if input('What?') == '1':
            p_code_node.set_rgb_led(100, 100, 100)
            p_code_node.scroll_text_in_array("HELLO")
            p_code_node.show_image_in_array(Icons().smile)
            p_code_node.show_image_in_array(Icons().sad)
            light_on = True
        else:
            p_code_node.reset()
            light_on = False

    p_code_node.set_sound_frequency(600)
    p_code_node.set_sound_frequency(300)
    p_code_node.reset()

if __name__ == "__main__":
    main()
