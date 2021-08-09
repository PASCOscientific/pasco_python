# README #

This library allows PASCO Wireless sensors to work with Python

## What is this repository for? ##

* PASCO Python Library
* Version 0.1

## How do I get set up? ##

Copy the library or at the minimum, the `pasco_ble.py` and `datasheets.xml` files.

Import the `PASCOBLEDevice` object from the pasco_ble file into your project file.

### 1) Initiate an object for the sensor ###
`my_sensor = PASCOBLEDevice()`

### 2) Scan for potential sensors ###
`my_sensor.scan()  # Returns list of BLE devices found in the scan.`

### 3) Connect to a sensor found from the scan ###
Connect to a BLE device found from the scan:  
`my_sensor.connect(ble_device)`

### Example of how to scan/connect ###
```
found_devices = my_sensor.scan()

print('\nDevices Found')
for i, ble_device in enumerate(found_devices):
    display_name = ble_device.name.split('>')
    print(f'{i}: {display_name[0]}')

# Auto connect if only one sensor found
selected_device = input('Select a device: ')
ble_device = found_devices[int(selected_device)]

my_sensor.connect(ble_device)
```

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

The down side of selecting all is that it will be a greater burden on the battery.

### If you want to specify the sensor ID to quickly connect ###
There are a few ways to quickly connect to the sensor. You can use the sensor name found in the scan *or* the 6 digit ID#. This will scan and connect to the sensor automatically.

Examples:  
`my_temp_sensor = PASCOBLEDevice('Temperature')`  
`my_weather_sensor = PASCOBLEDevice('Weather')`  
`my_temp_sensor = PASCOBLEDevice('111-123')`  
`my_weather_sensor = PASCOBLEDevice('222-345')`  

If you know you want to read JUST the light measurements from the Weather sensor we can use this:  
`my_weather_sensor = PASCOBLEDevice('Weather', 2)`  


### 4) Read sensor measurement data ###
The values inside the paranthesis represent the Dictionary variable names.

To read the `Temperature` we will say `my_sensor.value_of('Temperature')`  
To read the `RelativeHumidity` we will say `my_sensor.value_of('RelativeHumidity')`


## Let's put it all together ##
Example program to scan, select a sensor (we will use a Wireless Weather Sensor and read some measurements).

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

    my_sensor.connect(ble_device)
    # my_sensor.connect(ble_device,'a') # This will bypass the prompt and read all measurements

    my_sensor.value_of('Temperature')

```
