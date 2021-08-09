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

### Available Commands ###
`device = PASCOBLEDevice()` Create bluetooth sensor object  
`device.scan()` Scan for available bluetooth devices. Returns a list of available devices  
`device.connect()` Connect to a device using the name returned from the scan command.  
`device.potential_values()` Get a list of available variable names for the sensor  
`device.value_of()` Get a single measurement value  

---

### Step 1: Initiate an object for the sensor ###

`my_sensor = PASCOBLEDevice()`


### Step 2: Scan for available bluetooth (BLE) sensors ###

`my_sensor.scan()  # Returns list of BLE devices found in the scan.`  
`my_sensor.scan('Temperature') # Returns a list of Temperature sensors found`

How to use:  
`found_devices = my_sensor.scan()`


### Step 3: Connect to a BLE sensor found from the scan ###

Print a list of found devices (or use another option to browse the list)
```
for i, ble_device in enumerate(found_devices):
    display_name = ble_device.name.split('>')
    print(f'{i}: {display_name[0]}')
```
Connect to one of the devices:   
`my_sensor.connect(found_devices[0])`


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


### Step 4: Available sensor measurements ###

If a sensor only has one measurement, like the Wireless Temperature Sensor, we will see:
```
Connected to Temperature 111-123
WirelessTemperature (Temperature)
```

If a sensor has multiple measurements available you will be prompted to select which sensor measurements to activate. For example, if we try to connect to a Wireless Weather Sensor we will see:
```
Connected to Weather 222-345
0: Weather (Temperature, RelativeHumidity, AbsoluteHumidity, BarometricPressure, WindSpeed, DewPoint, WindChill, Humidex)
1: GPS (SatelliteCount, Latitude, Longitude, Altitude, Speed)
2: Light (UVIndex, Illuminance, SolarIrradiance, SolarPAR)
3: Compass (WindDirection, MagneticHeading, TrueHeading)
a: All
Enter [default: a]:
```

The values inside the paranthesis during the device measurement selection represent the measurement variable names (used in Step 5).

The down side of selecting all is that it will be a greater burden on the battery.


#### Connect to a sensor programatically ####

There are a few ways to quickly connect to the sensor. You can use the sensor name found in the scan *or* the 6 digit ID#. This will scan and connect to the sensor automatically. If multiple sensors with the same name are found, you will be prompted to select one.

Examples:  
`my_temp_sensor = PASCOBLEDevice('Temperature') # Looks for any available Temperature sensors`  
`my_weather_sensor = PASCOBLEDevice('Weather') # Looks for any available Weather sensor`  
`my_temp_sensor = PASCOBLEDevice('111-123') # Look for any sensor with this unique ID`  
`my_weather_sensor = PASCOBLEDevice('222-345') # Look for any sensor with this unique ID`  

If you know you want to read JUST the Light measurements from the Weather sensor we can use one of these methods:  
`my_weather_sensor = PASCOBLEDevice('Weather', 2)`  
`my_weather_sensor = PASCOBLEDevice('222-345', 2)`  

If we want the Weather and Light measurements from the weather sensor we can connect these ways:  
`my_weather_sensor = PASCOBLEDevice('Weather', '0,2')`  
`my_weather_sensor = PASCOBLEDevice('222-345', '0,2')`


### Step 5: Reading data from a sensor ###

The measurement variable names come from Step 4

To read the `Temperature`  
`my_temperature_sensor.value_of('Temperature')`  

To read the `RelativeHumidity`  
`my_weather_sensor.value_of('RelativeHumidity')`

---

## /\/code.Node Specific Commands ##

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
intensity range is 0-10
```

#### Set one LED  ####

`code_node_device.code_node_set_led(x, y, intensity)`  
Example: `code_node_device.code_node_set_led(2, 0, 10)` will turn the top center LED on at max brightness


#### Set multiple LEDs at once ####

`code_node_device.code_node_set_leds(led_array, intensity)`  
An example of an `led_array` is `[[4,4], [0,4], [2,2]]`


### Set the RGB LED ###

`code_node_device.code_node_set_rgb_leds(r, g, b)`  
`r`, `g`, `b` indicate brightness ranges between 0 and 10.


### Turn the speaker on/off ###

`code_node_device.code_node_set_sound_frequency(frequency)`  
Send `frequency` in Hz


### Reset the code_node outputs ###

`code_node_device.code_node_reset()`  
Turn the 5x5 LED display, RGB LED off and speaker off.

### The character library ###


#### Scroll Text ####

`code_node_device.code_node_scroll_text(string_to_scroll)`  
Scroll text on the 5x5 LED display. Requires importing the `character_library` to the project.

#### Display Icons ####
`code_node_device.code_node_show_icon(icon_name)`  
Show an icon on the 5x5 LED Display. Requires importing the `character_library` to the project. Refer to the library file to see available options.

---

## Let's put it all together ##

### Example 1: ###

Connect to a Wireless Temperature Sensor and get one reading:
```
from pasco_ble import PASCOBLEDevice

def main():
    my_temp_sensor = PASCOBLEDevice('835-041', 'a')
    
    temp_value = my_temp_sensor.value_of('Temperature')
    print(temp_value)

if __name__ == "__main__":
    main()
```

### Example 2: ###

Scan for a sensor and get the current temperature. In this example we can use a Temperature, Weather or /\/code.Node to read the temperature measurement so we don't want to specify a device. We want to constantly read and display the result.

```
from pasco_ble import PASCOBLEDevice

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

    my_sensor.connect(ble_device, 'a') # Read all measurements

    while True:
        current_temp = my_sensor.value_of('Temperature')
        print('The current temp is ' + str(current_temp))

if __name__ == "__main__":
    main()
```

### Example 3: ###

We can also connect to multiple sensors. Here we are connecting to a /\/code.Node and Wireless Force Sensor. We are also using /\/code.Node specific commands and testing the Character Library.

```
import character_library

from pasco_ble import PASCOBLEDevice


def main():
    code_node_device = PASCOBLEDevice('//code.Node','a')
    force_accel_device = PASCOBLEDevice('Force','a')

    code_node_device.code_node_reset()
    light_on = False

    while True:
        if force_accel_device.value_of('Force') > 10:
            if light_on == False:
                code_node_device.code_node_set_rgb_leds(5,5,5)
                code_node_device.code_node_set_sound_frequency(200)
                code_node_device.code_node_show_icon(character_library.Icons().alien)
                light_on = True
            else:
                code_node_device.code_node_reset()
                light_on = False
            while force_accel_device.value_of('Force') > 10:
                pass


if __name__ == "__main__":
    main()
```
