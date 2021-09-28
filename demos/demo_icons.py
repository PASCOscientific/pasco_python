import time

from pasco.character_library import Icons
from pasco.pasco_ble_device import PASCOBLEDevice

def main():

    # Connect to PASCO Device
    device = PASCOBLEDevice('//code.Node',0)

    while True:
        device.code_node_show_icon(Icons().smile)
        time.sleep(1)
        device.code_node_show_icon(Icons().sad)
        time.sleep(1)
        device.code_node_show_icon(Icons().surprise)
        time.sleep(1)
        device.code_node_show_icon(Icons().arrow_top)
        time.sleep(1)
        device.code_node_show_icon(Icons().arrow_topright)
        time.sleep(1)
        device.code_node_show_icon(Icons().arrow_right)
        time.sleep(1)
        device.code_node_show_icon(Icons().arrow_bottomright)
        time.sleep(1)
        device.code_node_show_icon(Icons().arrow_bottom)
        time.sleep(1)
        device.code_node_show_icon(Icons().arrow_bottomleft)
        time.sleep(1)
        device.code_node_show_icon(Icons().arrow_left)
        time.sleep(1)
        device.code_node_show_icon(Icons().arrow_topleft)
        time.sleep(1)
        device.code_node_show_icon(Icons().heart)
        time.sleep(1)
        device.code_node_show_icon(Icons().heart_sm)
        time.sleep(1)
        device.code_node_show_icon(Icons().alien)
        time.sleep(1)

if __name__ == "__main__":
    main()
