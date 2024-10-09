[![Python](https://img.shields.io/badge/python-3.11-blue)](https://pypi.org/project/pasco/)

![Platform](https://img.shields.io/badge/platform-windows%20%7C%20macos%20%7C%20linux-lightgrey)

# README

This PASCO Python library allows users to connect to PASCO Wireless sensors using Python. Create your own data collection application, use sensors to interact with other hardware devices, or come up with your own unique solution!

For project examples, view our [pasco_python_examples repository](https://github.com/PASCOscientific/pasco_python_examples).

# Contents:
- [Getting Started](#how-do-i-get-started)
- [Compatible Sensors](#compatible-sensors)
- [Connecting to a Sensor](#step-1-import-the-appropriate-module)
- [Collecting Data](#lets-put-it-all-together)
- [//code.Node](#codenode)
- [//control.Node](#controlnode)
- [Troubleshooting](#troubleshooting)

# How do I get started?

First, make sure you are working with Python 3.11 (see [Troubleshooting](#troubleshooting) for Python version help)

To install the PASCO package into your Python environment, type this into your Terminal

```
pip install pasco
```


In your project file, import the `PASCOBLEDevice` class, the `CodeNodeDevice` class, and/or the `ControlNodeDevice` class.




# Compatible Sensors

- /\/control.Node
- /\/code.Node
- Smart Cart
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


# Connecting to a sensor

## Device Structure

Device: A physical PASCO wireless sensor is a device.

Sensor: A device can have multiple sensors built in.

Measurements: A sensor can offer multiple measurements.

**Device Structure Example**

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
`device.connect_by_id(pasco_device_id: string)` Connect to a device using the 6 digit ID printed on the sensor.  
`device.disconnect()` Disconnect from a device  
`device.is_connected()` Returns true/false to tell device connection state  
`device.get_sensor_list()` Get a list of sensors that a device has  
`device.get_measurement_list(sensor_name: string [optional])` Returns all the measurements that a device has  
`device.read_data(measurement: string)` Get a single reading from a single measurement  
`device.read_data_list(measurements: List[string])` Get a list of readings for multiple measurements  
`device.get_measurement_unit(measurement: string)` Get the default units for a single measurement  
`device.get_measurement_unit_list(measurements: List[string])` Get a list of default units for multiple measurements


---

## Step 1: Import the appropriate module

For a regular wireless sensor:

```
from pasco.pasco_ble_device import PASCOBLEDevice
```

To connect to a /\/code.Node (Note: The Icons package is optional):

```
from pasco.code_node_device import CodeNodeDevice, Icons
```

To connect to a /\/control.Node:

```
from pasco.control_node_device import ControlNodeDevice
```

## Step 2: Create an object for the device

```
my_sensor = PASCOBLEDevice()
```

If you know the device's 6-digit serial ID (printed on the device) you can quickly scan and connect using the command:
`my_sensor.connect_by_id('111-123')`

Otherwise perform Steps 2 & 3 to scan/connect.

## Step 3: Scan for available bluetooth (BLE) sensors

`my_sensor.scan()` Returns list of BLE devices found in the scan. `my_sensor.scan('Temperature')` Returns a list of Temperature sensors found

How to use:

```
found_devices = my_sensor.scan()
```

## Step 4: Connect to a BLE sensor found from the scan

The scan command will return a list of found devices. Iterate through that list to determine which device you want to connect to.

One way is to print the list and prompt the user like this:

```
if found_devices:
    print('\nDevices Found')
    for i, ble_device in enumerate(found_devices):
        print(f'{i}: {ble_device.name}')

    selected_device = input('Select a device: ') if len(found_devices) > 1 else 0
    code_node_device.connect(found_devices[int(selected_device)])
else:
    print("No Devices Found")
    exit(1)
```

### Putting it all together:

```
from pasco.pasco_ble_device import PASCOBLEDevice

my_sensor = PASCOBLEDevice()
found_devices = my_sensor.scan()

if found_devices:
    print('\nDevices Found')
    for i, ble_device in enumerate(found_devices):
        print(f'{i}: {ble_device.name}')

    selected_device = input('Select a device: ') if len(found_devices) > 1 else 0
    my_sensor.connect(found_devices[int(selected_device)])
else:
    print("No Devices Found")
    exit(1)

print(f"measurements: {my_sensor.get_measurement_list()}")
my_sensor.disconnect()
```

## Step 5: View Device Sensor(s)

A device can have one or more on-board sensors. To view the list of sensors use the command `my_sensor.get_sensor_list()`. This returns a list of sensor names that a device has.

## Step 6: View Device Measurement(s)

Each sensor in the device can have one or more measurements. If you want to view all the measurements that a device has, use the command `my_sensor.get_measurement_list()`.

To view only the measurements that a sensor has, use the sensor name (from the list in Step 4) like this `my_sensor.get_measurement_list('WirelessWeatherSensor')`.

## Step 7: Start collecting data!

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

# Let's put it all together

##  Example: One shot read

```
from pasco.pasco_ble_device import PASCOBLEDevice


temp_sensor = PASCOBLEDevice()
temp_sensor.connect_by_id('055-808') # replace with your sensor's 6-digit id

temp_value = temp_sensor.read_data('Temperature')
temp_units = temp_sensor.get_measurement_unit('Temperature')
print(f'{temp_value} {temp_units}')

temp_sensor.disconnect()
```

## Example: Scan/select a sensor and read data

Scan for a sensor and get the current temperature. In this example we can use a Temperature, Weather or /\/code.Node to read the temperature measurement. We do not need to specify a device type. We will continuously read and display the result.

```
from pasco.pasco_ble_device import PASCOBLEDevice


my_sensor = PASCOBLEDevice()
found_devices = my_sensor.scan()

if found_devices:
    print('\nDevices Found')   
    for i, ble_device in enumerate(found_devices):
        print(f'{i}: {ble_device.name}')

    selected_device = input('Select a device: ') if len(found_devices) > 1 else 0
    my_sensor.connect(found_devices[int(selected_device)])
else:
    print("No Devices Found")
    exit(1)

# Loop that will read/display the data 100 times
for i in range(100):
    current_temp = my_sensor.read_data('Temperature')
    print(f'The current temp is {current_temp}')

my_sensor.disconnect()
```
---

# /\/code.Node

In order to connect to a /\/code.Node we must import the `CodeNodeDevice` object and (optionally) the character library which allows a user to display icons on the 5x5 LED Array.

```
from pasco.code_node_device import CodeNodeDevice, Icons
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

Example: This will turn the top center LED on at max brightness

```
code_node_device.set_led_in_array(2, 0, 255)
```

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



## Example: Working with the /\/code.Node

Below is a simple example that shows how to connect to a /\/code.Node, read a measurement and control an output.

```
from pasco.code_node_device import CodeNodeDevice


code_node = CodeNodeDevice()
code_node.connect_by_id('481-782') # replace with your device's 6-digit id

while code_node.read_data('Button1') == 0:
    if code_node.read_data('Brightness') < 2:
        code_node.set_rgb_led(100,100,100)
    else:
        code_node.set_rgb_led(0,0,0)

code_node.scroll_text_in_array('Goodbye')

code_node.reset()
code_node.disconnect()
```

## Example: Connect to multiple sensors

We can also connect to multiple sensors. Here we are connecting to a /\/code.Node and Wireless Force Sensor. We are also using /\/code.Node specific commands and testing the Character Library.

```
from pasco.pasco_ble_device import PASCOBLEDevice
from pasco.code_node_device import CodeNodeDevice, Icons


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

for i in range (1000):
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

code_node_device.disconnect()
force_accel_device.disconnect()
```
---
# /\/control.Node
The control node has an internal speaker and x,y,z acceleration sensor. But what makes the control node unique is that it can also connect to external devices such as a rangefinder, steppers, and servos. Any sensor plugged into the control node is automatically accessible just like a built-in sensor.

The control.Node has commands for setting steppers, servos, and the power output board as well as sensing from steppers, servos, and plugin sensors. 



If you know the 6-digit code of your control node device, you can just connect:

    from pasco.control_node_device import ControlNodeDevice
    import time

    controlNode = ControlNodeDevice()
    controlNode.connect_by_id('664-591') # replace with your device's 6-digit id

Now put the \/\/control.Node into the pascobot. Plug in the steppers into ports A and B on the \/\/control.Node, and run the following code. 

    from pasco.control_node_device import ControlNodeDevice
    import time

    controlNode = ControlNodeDevice()
    controlNode.connect_by_id('664-591') # replace with your device's 6-digit id
    
    controlNode.rotate_steppers_continuously(360, 360, 360, 360)
    time.sleep(1)
    controlNode.stop_steppers(360, 360)
    print(controlNode.read_data('Angle', 'A'))
    controlNode.disconnect()

This accelerates both steppers to 360 deg/s at an acceleration of 360 deg/s/s, waits a second, stops them at an acceleration of 360 deg/s/s, and reads the angle of stepper A.
More examples of steppers, servos, plugin sensors, and the power output board are in `controlnode_examples.py` and `grabberbot.py`.

---
# Troubleshooting

### 1. Are you working with Python 3.11?
To check your version type in your terminal
```
python --version
```
If that doesn't work try 
```
python3 --version
```
If that doesn't work you don't have python installed. Go to https://www.python.org/ and install.

If you have an older version of python installed, uninstall it and reinstall 3.11. 
After you reinstall Python you will also need to reinstall the pasco package. 
### 2. Is pasco installed?
If you get an error like `no module named "<module name>"` try
```
pip install pasco
``````

### 3. Is the device on?
Check if the red light is blinking. If so you're good to go.
### 4. Is the device already connected?
Check if the light is green. If so, hold down the power button to turn the device off, and press it to turn the device on again. When the light blinks red you're good.
### 5. Fire the intern.