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

### 2) Scan for available bluetooth (BLE) sensors ###
`my_sensor.scan()  # Returns list of BLE devices found in the scan.`

### 3) Connect to a sensor found from the scan ###
Connect to a BLE device found from the scan:  
`my_sensor.connect(ble_device)`

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

### Connect to a sensor programatically ###
There are a few ways to quickly connect to the sensor. You can use the sensor name found in the scan *or* the 6 digit ID#. This will scan and connect to the sensor automatically. If multiple sensors with the same name are found, you will be prompted to select one.

Examples:  
`my_temp_sensor = PASCOBLEDevice('Temperature')`  
`my_weather_sensor = PASCOBLEDevice('Weather')`  
`my_temp_sensor = PASCOBLEDevice('111-123')`  
`my_weather_sensor = PASCOBLEDevice('222-345')`  

If you know you want to read JUST the Light measurements from the Weather sensor we can use one of these methods:  
`my_weather_sensor = PASCOBLEDevice('Weather', 2)`  
`my_weather_sensor = PASCOBLEDevice('222-345', 2)`  

If we want the Weather and Light measurements from the weather sensor we can connect these ways:  
`my_weather_sensor = PASCOBLEDevice('Weather', '0,2')`  
`my_weather_sensor = PASCOBLEDevice('222-345', '0,2')`


### 4) Read sensor measurement data ###
The values inside the paranthesis represent the measurement variable names.

To read the `Temperature` we will say `my_temperature_sensor.value_of('Temperature')`  
To read the `RelativeHumidity` we will say `my_weather_sensor.value_of('RelativeHumidity')`


## Let's put it all together ##
Example 1: Connect to a Wireless Temperature Sensor and get one reading:
```
from pasco_ble import PASCOBLEDevice

def main():
    my_temp_sensor = PASCOBLEDevice('835-041', 'a')
    
    temp_value = my_temp_sensor.value_of('Temperature')
    print(temp_value)

if __name__ == "__main__":
    main()
```

Example 2: Scan for a sensor and get the current temperature. In this example we can use a Temperature, Weather or /\/code.Node to read the temperature measurement so we don't want to specify a device. We want to constantly read and display the result.

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

Example 3: 
