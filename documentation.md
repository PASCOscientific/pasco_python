# Documentation
### A more detailed description of how pasco python works
# Contents:
- [Background](#motivation)
- [`pasco_ble_device` under the hood](#pasco_ble_devicepy)
- [`control_node_device` under the hood](#control_node_devicepy)
# Motivation:
The goal of this python API is to connect a pasco device such as the control node to a python program. To do this we use bleak, a Bluetooth Low Energy (BLE) python library. Because communicating over bluetooth involves a time delay this involves using the asyncio library to handle asynchronous tasks such as reading and writing over bluetooth.
For more on these tools check out these links:
- bleak: https://nabeelvalley.co.za/docs/iot/bluetooth-intro/
- asyncio: 5-part tutorial: https://bbc.github.io/cloudfit-public-docs/asyncio/asyncio-part-1.html
---
# This API is made up of three layers:
1. `pasco_ble_device.py` is the base class for pasco devices, providing functionality for connecting, writing commands and reading data.
2. device-specific libraries such as `control_node_device.py` and `code_node_device.py` provide more specialized functionality for their devices such as controlling steppers, servos, and speakers. 
3. `pasco_bot.py` provides functionality for the pasco bot such as driving and turning.
---
# `pasco_ble_device.py`
This file does all the heavy lifting for the library, handling connecting to interfaces, initializing sensors, and all of the communication with the pasco devices. 
### Pasco devices consist of three layers:
1. Interface. This is the device you can hold, such as the control node. An interface can have many sensors, such as position, velocity, acceleration, light, temperature, etc.  
2. Sensors. These are the pieces of the interface you communicate with. Each sensor has its own bluetooth characteristic to receive commands and send data back to the computer. Each sensor has one to many measurements.
3. Measurements. These are the data requested and returned by the sensors, such as acceleration in the x direction or light intensity or temperature.

For the API, sensors are the most important layer, because they are where the BLE communication happens.

---
## BLE communication

Bluetooth Low Energy is a network protocol that allows the computer to communicate with pasco devices.

BLE communication consists of two steps: (1) the computer sends a `write` command to a sensor channel (a BLE `characteristic`) and in response (2) the device sends a `callback`. When the device is connected the computer starts 'listening' for callbacks, and `start_notify()` links the device's bluetooth callbacks to `_notify_callback()`, so that whenever the device sends a callback `_notify_callback()` runs. 

Let's look at an example of reading the light intensity from the code node:
1. The computer connects to the code node and starts 'listening' for callbacks.
2. The computer sends a `write` command to the light sensor characteristic on the code node, then waits to hear back.
3. The code node sends a callback with the data.
4. The computer receives the callback in `_notify_callback()`, processes the data, and continues execution.


### Synchronizing communication
It is very important that execution waits for a callback from the device because bluetooth communication takes an arbitrary amount of time. This synchronization is enabled by `write_await_callback()`. 

`write_await_callback()` uses tools from `asyncio` to package writing and receiving callbacks into a single task which blocks further execution until it completes. This task does the following:
1. It uses `write()` to send a command such as 'read light intensity'.
2. It calls `check_callback()` to wait for an `asyncio.Queue` object to be updated by `_notify_callback()`, indicating that a callback was received. 
3. Meanwhile, the callback is received and `_notify_callback()` updates the `Queue` object.
4. This unblocks `check_callback()` which in turn unblocks `write_await_callback()`, allowing execution to continue. 

---
## Initializing Device Sensors
Another key part of `pasco_ble_device.py` is how it represents the device internally. Recall that a pasco device consists of three layers:
1. The interface
2. Sensors available through the interface
3. Measurements provided by the sensors

When a pasco device connects it tells the computer its interface id, which is then looked up in `datasheets.py` This datasheet tells the computer what communication channels are available on the device, including sensors, outputs (like speakers), and plugin locations (such as the ports on the control node). This initializing is handled by `initialize_device()`. 

`initialize_device()` uses `datasheets.py` to first get data about the interface channels, then pass this to `initialize_device_sensors()`. This calls `_initialize_sensor()` on each sensor in turn to get data on the sensor and the measurements it provides. Finally the sensor and measurement lists are saved in several instance attributes.

### Plugin Sensors
Working with the control node's plugin sensors requires some special handling provided by several functions with `controlnode_plugins` in the name. 

The most important is `update_controlnode_plugin_sensor()`. When a sensor is plugged in or unplugged from the control node it sends a callback with the sensor IDs plugged into ports A, B, and Sensor. This callback is handled by `_notify_callback()`, which calls `process_measurement_response()`, which calls `update_controlnode_plugin_sensor()`. This unpacks the data about the sensors plugged in and passes the new sensor list to `initialize_device_sensors`, updating the internal sensor list. This process is initiated by `scan_controlnode_plugins()` during the control node's connect sequence, and repeated whenever a sensor is plugged in or unplugged from the control node.

---
# `control_node_device.py`
This file handles functionality specific to the control node. It inherits from `PASCOBLEDevice` and extends it to provide controls for the steppers, servos, power output board and speakers on the control node. 

### Reading Data
An important feature of the control node is the ability to plug in sensors, such as a range finder and two high speed steppers on the pasco bot. Unfortunately the internal representation of sensors and measurements in `pasco_ble_device.py` does not support a distinction between two of the same sensors plugged into two different ports. Because this is a control node specific issue we put the solution in `control_node_device.py`. 

In `ControlNodeDevice.read_data()` there is an optional parameter of port, allowing you to designate which port you want to read data from.  Consider `read_data(measurement='Angle', port='A')` sent to a pasco bot. The `Angle` measurement is available from the steppers in both ports `A` and `B`, so `read_data` uses the `port` parameter to designate which stepper from which to read the angle. Then when the callback comes for the `Angle` reading, we extract the measurement from the `_sensor_data` instance variable.

To read data from servos we also use the `port` parameter, but the data is unpacked and result calculated manually. 

### Steppers
There are three different types of commands sent to steppers:

1. Rotate stepper(s) continuously
2. Rotate stepper(s) through
3. Stop stepper(s)

`Rotate steppers` and `stop steppers` are a single command sent to the control node. `Rotate steppers through` is a little more complicated becase it has an optional argument `wait_for_completion`. If you set `wait_for_completion` to true it continuously checks the steps remaining, blocking further execution until it finishes the given rotation.

### Servos
Servos come in two flavors: continuous and standard. The standard servo rotates to a degree angle in [-90, 90], while the continuous servo rotates at a percent power in [-100, 100].
`set_servos()` takes arguments of servo types in servo ports 1 and 2 and values for those servos. Note that there is no `wait_for_completion` for servos, so you may have to add `time.sleep()` to allow them to finish.

Servos also can sense resistance. A call to `read_data('ServoCurrentOrd', 1)` reads the percent resistance experienced by the servo in port 1. This is useful for detecting when the grabber arms have grabbed something. See `grabberbot.py` for example uses.


### Power Board
The power board has two channels and can be plugged into port A or B. 
The two channels are independently controlled and can either output a PWM signal (for DC motors) or a 0V/5V signal (for USB devices). You control the power boards using `set_power_out`. 

Cool trick: plug an LED strip into the USB output, then call `set_power_out` on that channel with `output_type=terminal`. This will run PWM through the USB output, allowing you to dim the LED strip. This is fine for LED's but not for other devices.

### Plugin Sensors
Additional sensors (such as line follower, rangefinder, and greenhouse) can be plugged into the Sensor port. They work just like any other sensor, accessible by `read_data('measurement name')`. To find what measurements are available, call `<instance>.get_measurement_list()`