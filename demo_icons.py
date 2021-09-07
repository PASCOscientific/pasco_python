import time

from pasco_py_beta import PASCOBLEDevice
#from character_library import Icons
import character_library

def main():

    # Connect to PASCO Device
    device = PASCOBLEDevice('//code.Node',0)

    while True:
        device.code_node_show_icon(character_library.Icons().smile)
        time.sleep(1)
        device.code_node_show_icon(character_library.Icons().smile)
        time.sleep(1)
        device.code_node_show_icon(character_library.Icons().surprise)
        time.sleep(1)
        device.code_node_show_icon(character_library.Icons().arrow_top)
        time.sleep(1)
        device.code_node_show_icon(character_library.Icons().arrow_topright)
        time.sleep(1)
        device.code_node_show_icon(character_library.Icons().arrow_right)
        time.sleep(1)
        device.code_node_show_icon(character_library.Icons().arrow_bottomright)
        time.sleep(1)
        device.code_node_show_icon(character_library.Icons().arrow_bottom)
        time.sleep(1)
        device.code_node_show_icon(character_library.Icons().arrow_bottomleft)
        time.sleep(1)
        device.code_node_show_icon(character_library.Icons().arrow_left)
        time.sleep(1)
        device.code_node_show_icon(character_library.Icons().arrow_topleft)
        time.sleep(1)
        device.code_node_show_icon(character_library.Icons().heart)
        time.sleep(1)
        device.code_node_show_icon(character_library.Icons().heart_sm)
        time.sleep(1)
        device.code_node_show_icon(character_library.Icons().alien)
        time.sleep(1)

if __name__ == "__main__":
    main()
