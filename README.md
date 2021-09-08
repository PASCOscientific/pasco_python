# README #

This library allows PASCO Wireless sensors to work with Python

## What is this repository for? ##

* PASCO Python Library
* Version 0.1

## How do I get set up? ##

Copy the library or at the minimum, the `pasco_ble.py` and `datasheets.xml` files.

Import the `PASCOBLEDevice` object from the pasco_ble file into your project file.

## Connecting to a sensor ##

---

### Device Structure ###
Device: A single PASCO Bluetooth device/sensor
Sensor: A device can have multiple sensors
Measurements: A sensor can have multiple measurements

**Example**

A Wireless Weather Sensor would be a "device".
The "device" has 4 sensors  
`['WirelessWeatherSensor', 'WirelessGPSSensor', 'WirelessLightSensor', 'WirelessCompass']`

Each "sensor" can have multiple measurements  
- WirelessWeatherSensor: `['Temperature', 'RelativeHumidity', 'AbsoluteHumidity', 'BarometricPressure', 'WindSpeed', 'DewPoint', 'WindChill', 'Humidex']`
- WirelessGPSSensor: `['SatelliteCount', 'Latitude', 'Longitude', 'Altitude', 'Speed']`
- WirelessLightSensor: `['UVIndex', 'Illuminance', 'SolarIrradiance', 'SolarPAR']`
- WirelessCompass: `['WindDirection', 'MagneticHeading', 'TrueHeading']`


### Available Commands ###
`device = PASCOBLEDevice()` Create a Bluetooth device object  
`device.scan()` Scan for available bluetooth devices. Returns a list of available devices  
`device.connect()` Connect to a device using the name returned from the scan command.  
`device.connect_by_id()` Connect to a device using the name returned from the scan command.  
`device.disconnect()` Disconnect from a device  
`device.is_connected` Returns true/false to tell device connection state  
`device.get_sensor_list()` Get a list of sensors that a device has  
`device.get_measurement_list()` Returns all the measurements that a device has  
`device.read_data()` Get a single value from a single measurement  
`device.read_data_list()` Get a list of values for multiple measurements  
`device.get_measurement_unit()` Get a the default units for a single measurement  
`device.get_measurement_unit_list()` Get a list of default units for multiple measurements  

---

### Step 1: Initiate an object for the sensor ###

`my_sensor = PASCOBLEDevice()`

If you know the device's 6-digit serial ID (printed on the device) you can quickly scan and connect using the command:  
`my_sensor.connect_by_id('111-123')`

Otherwise perform Steps 2 & 3 to scan/connect.


### Step 2: Scan for available bluetooth (BLE) sensors ###

`my_sensor.scan()  # Returns list of BLE devices found in the scan.`  
`my_sensor.scan('Temperature') # Returns a list of Temperature sensors found`

How to use:  
`found_devices = my_sensor.scan()`


### Step 3: Connect to a BLE sensor found from the scan ###

The scan command will return a list of found devices. Iterate through that list to determine which device you want to connect to.

One way is to print the list and prompt the user like this:
```
for i, ble_device in enumerate(found_devices):
    print(f'{i}: {ble_device.name}')

selected_device = input('Select a device: ') 
my_sensor.connect(found_devices[int(selected_device)])

```

### Example of how to scan/connect ###

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


### Step 4: View Device Sensor(s) ###

A device can have one or more on-board sensors. To view the list of sensors use the command `my_sensor.get_sensor_list()`. This returns a list of sensor names that a device has.


### Step 5: View Device Measurement(s) ###

Each sensor can have one or more measurements. If you want to view all the measurements that a device has, use the command `my_sensor.get_measurement_list()`.  

To view only the measurements that a sensor has, use the sensor name (from the list in Step 4) like this `my_sensor.get_measurement_list('WirelessWeatherSensor')`.


### Step 6: Start collecting data! ###

The measurement variable names come from Step 4

To read the `Temperature`  
`my_temperature_sensor.read_data('Temperature')`  

To read the `RelativeHumidity`  
`my_weather_sensor.read_data('RelativeHumidity')`

To read a list of measurements  
`my_weather_sensor.read_data_list(['Temperature','RelativeHumidity'])`

To get the units for a measurement  
`my_temperature_sensor.get_measurement_unit('Temperature')`

To get the units for a list of measurements  
`my_weather_sensor.get_measurement_unit_list(['Temperature','RelativeHumidity'])`

---

## /\/code.Node Specific Commands ##

In order to connect to a /\/code.Node we must import the `CodeNodeDevice` object and (optionally) the character library which allows a user to display text on the 5x5 LED Array.

```
from code_node_device import CodeNodeDevice
import character_library
```
`my_code_node = CodeNodeDevice()` Create /\/code.Node Bluetooth device object  
`my_code_node.set_led_in_array()` Set an individual LED in the 5x5 LED Array  
`my_code_node.set_leds_in_array()` Set multiple LEDs in the 5x5 LED Array  
`my_code_node.set_rgb_led()` Set the RGB LED  
`my_code_node.set_sound_frequency()` Set the speaker frequency  
`my_code_node.scroll_text_in_array` Scroll text on the 5x5 LED Array  
`my_code_node.show_image_in_array()` Display an image in the 5x5 LED Array  
`my_code_node.reset()` Reset all of the /\/code.Node outputs  


### Set LEDs on the 5x5 Display ###

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

#### Set one LED  ####

`code_node_device.set_led_in_array(x, y, intensity)`  
Example: `code_node_device.set_led_in_array(2, 0, 255)` will turn the top center LED on at max brightness


#### Set multiple LEDs at once ####

`code_node_device.set_leds_in_array(led_array, intensity)`

```
led_array = [[4,4], [0,4], [2,2]]
code_node_device.set_leds_in_array(led_array, 128)
```

### Set the RGB LED ###

`code_node_device.set_rgb_led(r, g, b)`  
`r`, `g`, `b` indicate brightness ranges between 0 and 255.

```
r = 20
g = 100
b = 200
code_node_device.set_rgb_led(r, g, b)
```

### Turn the speaker on/off ###

`code_node_device.set_sound_frequency(frequency)`  
Send `frequency` (int) in Hz

```
code_node_device.set_sound_frequency(440)
```


### Scroll Text on the 5x5 LED Array ###

`code_node_device.scroll_text_in_array(text)`  
This will scroll the text on the /\/code.Node's display

```
code_node_device.scroll_text_in_array('HELLO WORLD')
```

### The character library ###

`code_node_device.show_image_in_array(character_library.Icons().smile)`  
If we import the `character_library` to our project we can show unique images on the display. Refer to the library file to see available options. Examples:

```
code_node_device.show_image_in_array(character_library.Icons().smile)
code_node_device.show_image_in_array(character_library.Icons().heart)
```

### Reset the code_node outputs ###

`code_node_device.reset()`  
Turn the 5x5 LED display, RGB LED off and speaker off.

---

## Let's put it all together ##

### Example 1: ###

Connect to a Wireless Temperature Sensor and get one reading:
```
from pasco_py_beta import PASCOBLEDevice

def main():
    my_temp_sensor = PASCOBLEDevice()
    my_temp_sensor.connect_by_id('055-808')
    
    temp_value = my_temp_sensor.read_data('Temperature')
    temp_units = my_temp_sensor.get_measurement_unit('Temperature')

    print(f'{temp_value} {temp_units}')

if __name__ == "__main__":
    main()
```

### Example 2: ###

Scan for a sensor and get the current temperature. In this example we can use a Temperature, Weather or /\/code.Node to read the temperature measurement so we don't want to specify a device. We want to constantly read and display the result.

```
from pasco_py_beta import PASCOBLEDevice

def main():
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

    while True:
        current_temp = my_sensor.read_data('Temperature')
        print(f'The current temp is {current_temp}')

if __name__ == "__main__":
    main()
```

### Example 3: ###

We can also connect to multiple sensors. Here we are connecting to a /\/code.Node and Wireless Force Sensor. We are also using /\/code.Node specific commands and testing the Character Library.

```
from pasco_py_beta import PASCOBLEDevice
from code_node_device import CodeNodeDevice
import character_library


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
                code_node_device.show_image_in_array(character_library.Icons().alien)
                light_on = True
            else:
                code_node_device.reset()
                light_on = False
            while force_accel_device.read_data('Force') > 10:
                pass

if __name__ == "__main__":
    main()
```
