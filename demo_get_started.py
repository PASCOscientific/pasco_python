import time

from pasco_py_beta import PASCOBLEDevice
#from character_library import Icons
import character_library

def main():

    device = PASCOBLEDevice()

    found_devices = device.scan()

    if len(found_devices) == 0:
        print("No devices found")
        exit(1)

    print('Devices Found')
    for i, ble_device in enumerate(found_devices):
        display_name = ble_device.name.split('>')
        print(f'{i}: {display_name[0]}')

    # Auto connect if only one sensor found
    selected_device = input('Select a device: ') if len(found_devices) > 1 else 0
    ble_device = found_devices[int(selected_device)]
    
    device.connect(ble_device)
    device.get_sensor_list()
    device.get_measurement_list()

    result_value = device.read_measurement_data('Temperature')
    result_unit = device.get_measurement_unit('Temperature')

    print(f'{result_value} {result_unit}')


if __name__ == "__main__":
    main()
