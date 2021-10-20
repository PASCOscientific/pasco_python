[![Python](https://img.shields.io/badge/python-3.7%20%7C%203.8-blue)](https://pypi.org/project/pasco/)

# README

This library allows PASCO Wireless sensors to work with Python

# What is this repository for?

- PASCO Python Library
- Version 0.1.0

# How do I get started?

```
pip install pasco
```

In your project file, import the device class and/or the code node device class

```
from pasco.pasco_ble_device import PASCOBLEDevice
from pasco.code_node_device import CodeNodeDevice
from pasco.character_library import Icons
```

# Compatible Sensors

- /\/code.Node
- Wireless Acceleration Altimter
- Wireless CO2
- Wireless Conductivity
- Wireless Current
- Wireless Diffraction
- Wireless Drop Counter
- Wireless Force Acceleration
- Wireless Light
- Wireless Load Cell
- Wireless Magnetic Field
- Wireless Motion
- Wireless O2
- Wireless Optical DO
- Wireless pH
- Wireless Pressure
- Wireless Rotary Motion
- Wireless Smart Cart
- Wireless Temperature
- Wireless Voltage
- Wireless Weather

Testing

- Wireless Blood Pressure
- Wireless Soil Moisture

# Connecting to a sensor

## Device Structure

Device: A physical PASCO wireless sensor is a device  
Sensor: A device can have multiple sensors built in  
Measurements: A sensor can offer multiple measurements

**Example**

A Wireless Weather Sensor would be a "device".
The "device" has 4 sensors  
`['WirelessWeatherSensor', 'WirelessGPSSensor', 'WirelessLightSensor', 'WirelessCompass']`

Each "sensor" can have multiple measurements

- WirelessWeatherSensor: `['Temperature', 'RelativeHumidity', 'AbsoluteHumidity', 'BarometricPressure', 'WindSpeed', 'DewPoint', 'WindChill', 'Humidex']`
- WirelessGPSSensor: `['SatelliteCount', 'Latitude', 'Longitude', 'Altitude', 'Speed']`
- WirelessLightSensor: `['UVIndex', 'Illuminance', 'SolarIrradiance', 'SolarPAR']`
- WirelessCompass: `['WindDirection', 'MagneticHeading', 'TrueHeading']`

### Available Commands

`device = PASCOBLEDevice()` Create a Bluetooth device object  
`device.scan(sensor_name_filter: string [optional])` Scan for available bluetooth devices. Returns a list of available devices  
`device.connect(ble_device: BLEDevice)` Connect to a device using the object returned from the scan command.  
`device.connect_by_id(pasco_device_id: string)` Connect to a device using the name returned from the scan command.  
`device.disconnect()` Disconnect from a device  
`device.is_connected` Returns true/false to tell device connection state  
`device.get_sensor_list()` Get a list of sensors that a device has  
`device.get_measurement_list(sensor_name: string [optional])` Returns all the measurements that a device has  
`device.read_data(measurement: string)` Get a single reading from a single measurement  
`device.read_data_list(measurements: List[string])` Get a list of readings for multiple measurements  
`device.get_measurement_unit(measurement)` Get the default units for a single measurement  
`device.get_measurement_unit_list(measurements: List[string])` Get a list of default units for multiple measurements

PASCO's Bluetooth sensors will turn off after 5 minutes of no activity. To keep the device on, call the `device.keepalive()` method. This will keep the connection active without requesting any new data.

---

## Step 1: Create an object for the device

`my_sensor = PASCOBLEDevice()`

If you know the device's 6-digit serial ID (printed on the device) you can quickly scan and connect using the command:  
`my_sensor.connect_by_id('111-123')`

Otherwise perform Steps 2 & 3 to scan/connect.

## Step 2: Scan for available bluetooth (BLE) sensors

`my_sensor.scan() # Returns list of BLE devices found in the scan.`  
`my_sensor.scan('Temperature') # Returns a list of Temperature sensors found`

How to use:  
`found_devices = my_sensor.scan()`

## Step 3: Connect to a BLE sensor found from the scan

The scan command will return a list of found devices. Iterate through that list to determine which device you want to connect to.

One way is to print the list and prompt the user like this:

```
for i, ble_device in enumerate(found_devices):
    print(f'{i}: {ble_device.name}')

selected_device = input('Select a device: ')
my_sensor.connect(found_devices[int(selected_device)])

```

### Example of how to scan/connect

```
my_sensor = PASCOBLEDevice()
found_devices = my_sensor.scan()

print('\nDevices Found')
for i, ble_device in enumerate(found_devices):
    display_name = ble_device.name.split('>')
    print(f'{i}: {display_name[0]}')

# Auto connect if only one sensor found
selected_device = input('Select a device: ') if len(found_devices) > 1 else 0
ble_device = found_devices[int(selected_device)]

my_sensor.connect(ble_device)
```

## Step 4: View Device Sensor(s)

A device can have one or more on-board sensors. To view the list of sensors use the command `my_sensor.get_sensor_list()`. This returns a list of sensor names that a device has.

## Step 5: View Device Measurement(s)

Each sensor in the device can have one or more measurements. If you want to view all the measurements that a device has, use the command `my_sensor.get_measurement_list()`.

To view only the measurements that a sensor has, use the sensor name (from the list in Step 4) like this `my_sensor.get_measurement_list('WirelessWeatherSensor')`.

## Step 6: Start collecting data!

The measurement variable names come from Step 4

To read the `Temperature`  
`my_temperature_sensor.read_data('Temperature')`

To read the `RelativeHumidity`  
`my_weather_sensor.read_data('RelativeHumidity')`

To read a multiple measurements at one time  
`my_weather_sensor.read_data_list(['Temperature','RelativeHumidity'])`

To get the units for a single measurement  
`my_temperature_sensor.get_measurement_unit('Temperature')`

To get the units for a list of measurements  
`my_weather_sensor.get_measurement_unit_list(['Temperature','RelativeHumidity'])`

---

## /\/code.Node Specific Commands

In order to connect to a /\/code.Node we must import the `CodeNodeDevice` object and (optionally) the character library which allows a user to display icons on the 5x5 LED Array.

```
from pasco.code_node_device import CodeNodeDevice
from pasco.character_library import Icons
```

`my_code_node = CodeNodeDevice()` Create /\/code.Node Bluetooth device object  
`my_code_node.set_led_in_array()` Set an individual LED in the 5x5 LED Array  
`my_code_node.set_leds_in_array()` Set multiple LEDs in the 5x5 LED Array  
`my_code_node.set_rgb_led()` Set the RGB LED  
`my_code_node.set_sound_frequency()` Set the speaker frequency  
`my_code_node.scroll_text_in_array` Scroll text on the 5x5 LED Array  
`my_code_node.show_image_in_array()` Display an image in the 5x5 LED Array  
`my_code_node.reset()` Reset all of the /\/code.Node outputs

### Set LEDs on the 5x5 Display

```
x, y coordinates on the //code.Node 5x5 LED display
---------------------------
| 0,0  1,0  2,0  3,0  4,0 |
| 0,1  1,1  2,1  3,1  4,1 |
| 0,2  1,2  2,2  3,2  4,2 |
| 0,3  1,3  2,3  3,3  4,3 |
| 0,4  1,4  2,4  3,4  4,4 |
---------------------------
intensity range is 0-255
```

### Set one LED

`code_node_device.set_led_in_array(x, y, intensity)`  
Example: `code_node_device.set_led_in_array(2, 0, 255)` will turn the top center LED on at max brightness

### Set multiple LEDs at once

`code_node_device.set_leds_in_array(led_list, intensity)`

```
led_list = [[4,4], [0,4], [2,2]]
code_node_device.set_leds_in_array(led_list, 128)
```

### Set the RGB LED

`code_node_device.set_rgb_led(r, g, b)`  
`r`, `g`, `b` indicate brightness ranges between 0 and 255.

```
r = 20
g = 100
b = 200
code_node_device.set_rgb_led(r, g, b)
```

### Turn the speaker on/off

`code_node_device.set_sound_frequency(frequency)`  
Send `frequency` (int) in Hz

```
code_node_device.set_sound_frequency(440)
```

Turn the speaker off

```
code_node_device.set_sound_frequency(0)
```

### Scroll Text on the 5x5 LED Array

`code_node_device.scroll_text_in_array(text)`  
This will scroll the text on the /\/code.Node's display

```
code_node_device.scroll_text_in_array('HELLO WORLD')
```

### The character library

`code_node_device.show_image_in_array(Icons().smile)`  
If we import the `Icons` class from the `character_library` to our project we can show unique images on the 5x5 LED Array. Refer to the library file to see available options. Examples:

```
code_node_device.show_image_in_array(Icons().smile)
code_node_device.show_image_in_array(Icons().heart)
```

### Reset the code_node outputs

`code_node_device.reset()`  
Turn the 5x5 LED display, RGB LED and speaker off.

# Let's put it all together

## Example 1: One shot read

Connect to a Wireless Temperature Sensor and get one reading:

```
from pasco.pasco_ble_device import PASCOBLEDevice

def main():
    temp_sensor = PASCOBLEDevice()
    temp_sensor.connect_by_id('055-808') # Your sensor's 6-digit ID

    temp_value = temp_sensor.read_data('Temperature')
    temp_units = temp_sensor.get_measurement_unit('Temperature')

    print(f'{temp_value} {temp_units}')

if __name__ == "__main__":
    main()
```

## Example 2: Scan/select a sensor and read data

Scan for a sensor and get the current temperature. In this example we can use a Temperature, Weather or /\/code.Node to read the temperature measurement. We do not need to specify a device type. We will continuously read and display the result.

```
from pasco.pasco_ble_device import PASCOBLEDevice

def main():
    my_sensor = PASCOBLEDevice()
    found_devices = my_sensor.scan()

    print('\nDevices Found')
    for i, ble_device in enumerate(found_devices):
        display_name = ble_device.name.split('>') # Cut off the unnecessary bits of the name
        print(f'{i}: {display_name[0]}')

    # Auto connect if only one sensor found
    selected_device = input('Select a device: ') if len(found_devices) > 1 else 0

    ble_device = found_devices[int(selected_device)]

    my_sensor.connect(ble_device)

    # Endless loop that will read/display the data
    while True:
        current_temp = my_sensor.read_data('Temperature')
        print(f'The current temp is {current_temp}')

if __name__ == "__main__":
    main()
```

## Example 3: Connect to multiple sensors

We can also connect to multiple sensors. Here we are connecting to a /\/code.Node and Wireless Force Sensor. We are also using /\/code.Node specific commands and testing the Character Library.

```
from pasco.pasco_ble_device import PASCOBLEDevice
from pasco.code_node_device import CodeNodeDevice
from pasco.character_library import Icons

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

    force_accel_device = PASCOBLEDevice()
    found_devices = force_accel_device.scan('Force')

    if found_devices:
        for i, ble_device in enumerate(found_devices):
            print(f'{i}: {ble_device.name}')

        selected_device = input('Select a device: ') if len(found_devices) > 1 else 0
        force_accel_device.connect(found_devices[int(selected_device)])
    else:
        print("No Devices Found")
        exit(1)

    code_node_device.reset()
    light_on = False

    while True:
        if force_accel_device.read_data('Force') > 10:
            if light_on == False:
                code_node_device.set_rgb_led(100,100,100)
                code_node_device.set_sound_frequency(200)
                code_node_device.show_image_in_array(Icons().alien)
                light_on = True
            else:
                code_node_device.reset()
                light_on = False
            while force_accel_device.read_data('Force') > 10:
                pass

if __name__ == "__main__":
    main()
```
