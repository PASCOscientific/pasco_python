from pasco.character_library import Icons
from pasco.code_node_device import CodeNodeDevice
from pasco.pasco_ble_device import PASCOBLEDevice


def main():

    code_node_device = CodeNodeDevice()
    found_devices = code_node_device.scan('//code.Node')

    if found_devices:
        for i, ble_device in enumerate(found_devices):
            print(f'{i}: {ble_device.name}')
        
        selected_device = input('Select a device: ') if len(found_devices) > 1 else 0
        code_node_device.connect(found_devices[int(selected_device)])
    else:
        print("No Devices Found")
        exit(1)

    light_on = False
    while True:

        if light_on == False:
            code_node_device.set_rgb_led(100,100,100)
            code_node_device.set_sound_frequency(200)
            code_node_device.scroll_text_in_array('Hello World')
            code_node_device.show_image_in_array(Icons().alien)
            light_on = True
        else:
            code_node_device.reset()
            light_on = False


if __name__ == "__main__":
    main()