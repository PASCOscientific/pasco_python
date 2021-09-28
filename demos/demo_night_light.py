from pasco.pasco_ble_device import PASCOBLEDevice

def main():

    # Connect to PASCO Device
    device = PASCOBLEDevice('//code.Node',0)

    while (device.value_of('Button1') == 0):
        if (device.value_of('Brightness') < 1):
            device.code_node_set_rgb_leds(5,5,5)
        else:
            device.code_node_set_rgb_leds(0,0,0)

if __name__ == "__main__":
    main()
