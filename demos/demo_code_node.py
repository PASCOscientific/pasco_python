from pasco import CodeNodeDevice, Icons
from random import random


def main():
    # Connect to PASCO Device
    p_code_node = CodeNodeDevice()
    p_code_node.connect_by_id('//code.Node')

    p_code_node.reset()

    while p_code_node.read_data('Button1') == 0:
        p_code_node.set_rgb_led(100, 100, 100)
        p_code_node.scroll_text_in_array("HELLO")
        p_code_node.show_image_in_array(Icons().smile)
        p_code_node.show_image_in_array(Icons().sad)

    measurements = p_code_node.get_measurement_list()

    print(measurements)

    for m in measurements:
        #p_code_node.set_rgb_led(int(10*random()),int(10*random()),int(10*random()))
        print(p_code_node.read_data(m))
 
    p_code_node.reset()

    p_code_node.set_sound_frequency(600)
    p_code_node.set_sound_frequency(300)
    p_code_node.reset()

if __name__ == "__main__":
    main()
