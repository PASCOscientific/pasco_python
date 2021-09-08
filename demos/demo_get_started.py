from pasco_ble_device import PASCOBLEDevice
from bleak.backends.device import BLEDevice
import time
import asyncio

def main():

    device = PASCOBLEDevice()

    found_devices = device.scan()

    if len(found_devices) == 0:
        print("No devices found")
        exit(1)

    print('Devices Found')
    for i, ble_device in enumerate(found_devices):
        #print(ble_device.address)
        print(f'{i}: {ble_device.name}')
    '''
    for i, ble_device in enumerate(found_devices):
        #print(ble_device.address)
        display_name = ble_device.name.split('>')
        print(f'{i}: {display_name[0]}')
    '''

    # Auto connect if only one sensor found
    selected_device = input('Select a device: ') if len(found_devices) > 1 else 0
    ble_device = found_devices[int(selected_device)]
    device.connect(ble_device)

    # Read the sensors that a device has
    sensors = device.get_sensor_list()
    print(sensors)
    
    # Read the measurements a device can read
    all_measurements = device.get_measurement_list()
    print(all_measurements)

    # Read the measurements from a specific sensor (pass in the sensor parameter from get_sensor_list function)
    #weather_measurement_list = device.get_measurement_list('WirelessWeatherSensor')
    #print(weather_measurement_list)

    print(device.get_measurement_list('WirelessWeatherSensor'))
    print(device.get_measurement_list('WirelessGPSSensor'))
    print(device.get_measurement_list('WirelessLightSensor'))
    print(device.get_measurement_list('WirelessCompass'))
    
    temperature_measurement_list = device.get_measurement_list('WirelessTemperatureSensor')
    print(temperature_measurement_list)

    #result_unit = device.get_measurement_unit('DewPoint')
    #result_value = device.read_data('DewPoint')
    #print(f'{result_value} {result_unit}')

    stamp = time.time()
    while True:
        if time.time() > stamp + 30:
            stamp = time.time()
            #result_unit = device.get_measurement_unit(['Temperature','Latitude','DewPoint','HeatIndex','WindChill'])
            result_unit = device.get_measurement_unit(['Temperature'])
            result_value = device.read_data_list(['Temperature'])
            print(f'{result_value} {result_unit}')


if __name__ == "__main__":
    main()
