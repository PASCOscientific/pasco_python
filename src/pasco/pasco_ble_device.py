import asyncio
import math
import nest_asyncio
import os
import sys
import re
import time
import struct
import xml.etree.ElementTree as ET

from bleak import BleakClient, BleakGATTCharacteristic, BleakScanner
from bleak.backends.device import BLEDevice
from .datasheets import datasheet
from uuid import UUID


class PASCOBLEDevice():
    """
    PASCO Device object that has functions for connecting and getting data
    """
    
    nest_asyncio.apply() # Fixes a glitch where some IDEs block asyncio from running

    SENSOR_SERVICE_ID = 0

    SEND_CMD_CHAR_ID = 2
    RECV_CMD_CHAR_ID = 3
    SEND_ACK_CHAR_ID = 5

    GCMD_CUSTOM_CMD = 0x37
    GCMD_READ_ONE_SAMPLE = 0x05
    GCMD_XFER_BURST_RAM = 0X0E

    # connection sequence commands for control Node
    CNTRLNODE_PLUGINS_CALLBACK = 0x82
    CTRLNODE_CMD_DETECT_DEVICES = 8         # Detects which devices are attached
    GCMD_CONTROL_NODE_CMD = 0x37

    GRSP_RESULT = 0XC0                      # Generic response packet
    GEVT_SENSOR_ID = 0x82                   # Get Sensor ID (for AirLink)

    WIRELESS_RMS_START = [0X37, 0X01, 0X00]

    def __init__(self):
        """
        Create a PASCO BLE Device object
        """

        self._client = None
        self._address = None
        self._name = None
        self._serial_id = None
        self._interface_id = None
        self._airlink_sensor_id = None
        self._type = "BLE"
        self._loop = asyncio.new_event_loop()
        self._queue = asyncio.Queue()       # this is used to synchronize with the callback
        self._data_ack_counter = {}

        # sensor and measurement data
        self._sensor_names = []             # {sensor name: sensor object}
                                            # this causes problems with multiple of the same sensor
        self._device_measurements = {}      # {sensor_channel: {measurementID: measurement attrs}}
                                            # stores measurements available through each sensor on the device
        self._handle_service = {}           # Array to lookup BLE service id with the handle
        self._data_stack = {}               # {sensor_channel: [data from sensor_channel]}
                                            # used to organize data packets by sensor channel as they come in
        self._data_packet = []              # [raw data]
        self._response_data = bytearray()   # response_data holds the data from the device callback
        self._sensor_data = {}              # {sensor_channel: {measurementID: measurement value}}
        self._sensor_data_prev = {}         # {sensor_channel: {measurementID: measurement value previous}}
        self._rotary_pos_data = {}          # apparently unused. 

        self._notify_sensor_id = None       # apparently unused.
        self._data_results = {}             # {measurement name: human-readable data}
                                            # stores sensor readings organized by measurement
                                            # this causes problems with multiple of the same sensor
        self._measurement_sensor_ids = {}   # {measurement name: sensor channel at which measurement can be requested}
                                            # This causes problems with multiple of the same sensor

        # Load Datasheet
        # it is saved as a string literal variable in datasheets.py
        self._xml_root = ET.fromstring(datasheet)

        self._compatible_devices = [
            '//code.Node',
            'Accel Alt',
            'CO2',
            'Conductivity',
            '//control.Node',
            'Current',
            'Diffraction',
            'Drop Counter',
            'Force Accel',
            'Light',
            'Load Cell',
            'Mag Field',
            'Motion',
            'O2',
            'Optical DO',
            'pH',
            'Pressure',
            'Rotary Motion',
            'Smart Cart',
            'Temperature',
            'Voltage',
            'Weather',
        ]

        """
        self._not_compatible_devices = [
            'BP',
            'Smart Gate',
            'Sound',
            'EKG',
            'Melt Temp',
            'Moisture',
            'Colorimeter',
            'AC/DC Module',
            'LightSource',
            'STEM Module',
            'AirLink',
            'Geiger',
            'Spirometer',
            'CO',
        ]
        """


    @property
    def name(self):
        return self._name
        
    @property
    def serial_id(self):
        return self._serial_id

    @property
    def client(self):
        return self._client

    @property
    def address(self):
        return self._address

    @property
    def data_results(self):
        return self._data_results

    @property
    def device_sensors(self):
        return self._sensor_names


# ---------- Connecting ----------


    def scan(self, sensor_name_filter=None):
        """
        Scans for all PASCO devices

        Args:
            sensor_name_filter (string, optional): Sensor name to scan for

        Returns:
            List of devices that are compatible with this library
        """
    
        try:
            # Get list of PASCO BLE Devices found
            if sensor_name_filter:
                pasco_device_names = [ sensor_name_filter ]
            else:
                pasco_device_names = self._compatible_devices

            found_devices = self._loop.run_until_complete(self._async_scan(pasco_device_names))

            return found_devices

        except:
            raise self.BLEScanFailed()


    async def _async_scan(self, pasco_device_names):
        """
        INTERNAL
        Scans for BLE devices and returns a list of pasco devices available to connect to
        Args:
            pasco_device_names (list[str]): list of pasco devices to scan for

        """
        found_devices = []
        
        bleak_devices = await BleakScanner.discover() #returns array of all devices found via bluetooth scan

        for ble_device in bleak_devices:
            for pasco_device_name in pasco_device_names:
                if ble_device.name and pasco_device_name in ble_device.name and ble_device not in found_devices:
                    found_devices.append(ble_device)

        return found_devices


    def _get_notify_uuids(self) -> list[UUID]:
        """
        Create a list of UUIDs for characteristics who have a notify property.
        This will be used to enable notifications from all of these characteristics
            in the connect method
        
        Returns:
            list of uuid objects
        """
        uuids = []

        services = self._client.services
        for service in services:
            chars = service.characteristics
            for char in chars:
                if 'notify' in char.properties:
                    uuids.append(UUID(char.uuid))

        # print(uuids)
        return uuids


    def connect(self, ble_device: BLEDevice):
        """
        Connect to a bluetooth device

        Args:
            ble_device (BLEDevice): BLE device to connect to (discovered during scan)
        """
    
        if ble_device is None:
            raise self.InvalidParameter

        if self._client is not None:
            raise self.BLEAlreadyConnectedError('Device already connected')

        self._client = BleakClient(ble_device.address)

        try:
            self._loop.run_until_complete(self._async_connect())
            # self.keepalive()
        except:
            raise self.BLEConnectionError('Could not connect to the sensor')

        self._set_device_params(ble_device)

        if (self._dev_type == "Rotary Motion"):
            self._loop.run_until_complete(self.write_await_callback(self.SENSOR_SERVICE_ID, self.WIRELESS_RMS_START))

        self.initialize_device()


    def connect_by_id(self, pasco_device_id):
        """
        Connect to a bluetooth device using the 6 digit ID printed on the case

        Args:
            pasco_device_id (string): Device's 6 digit ID (with dash)
        """
        
        if pasco_device_id is None:
            raise self.InvalidParameter
    
        if self._client is not None:
            raise self.BLEAlreadyConnectedError()

        try:
            found_devices = self.scan(pasco_device_id)
            if found_devices:
                ble_device = found_devices[0]
                self.connect(ble_device)
            else:
                raise self.BLEConnectionError
        except:
            raise self.BLEConnectionError


    async def _async_connect(self):
        await self._client.connect()
        if not self._client.is_connected:
            return False

        self._set_handle_service()

        uuids = self._get_notify_uuids()
        # start receiving notifications from all characteristics that notify
        for uuid in uuids:
            await self._client.start_notify(uuid, self._notify_callback)


    def keepalive(self):
        self._loop.run_until_complete(self.write_await_callback(self.SENSOR_SERVICE_ID, [0x00]))


    def is_connected(self):
        """
        Returns boolean for the connection state
        """
        if self._client != None:
            return self._client.is_connected


    def disconnect(self):
        """
        Disconnect from the device
        """
        if self._client != None:
            self._loop.run_until_complete(self._client.disconnect())
        self._client = None   


# ---------- Initializing ----------


    def _set_handle_service(self):
        """ Create dictionary to to lookup service_id given the ble device handle """
        for service in self._client.services:
            for characteristic in service.characteristics:
                if characteristic.uuid[7].isnumeric():
                    self._handle_service[characteristic.handle] = int(characteristic.uuid[7])


    def _set_uuid(self, service_id, characteristic_id):
        """
        Create UUID for service and characteristic

        Args:
            service_id: The sensor service we're connecting to
            characteristic_id: The characteristic we want to communicate with
        
        Returns:
            uuid object
        """
    
        uuid = "4a5c000" + str(service_id) + "-000" + str(characteristic_id) + "-0000-0000-5c1e741f1c00"
        return UUID(uuid)
    

    def scan_controlnode_plugins(self):
        """
        Detect the devices that are attached to the control node.
        This will trigger a cascading update of available control node sensors
        """
        if self.is_connected() is False:
            raise self.DeviceNotConnected()

        cmd = [ self.CTRLNODE_CMD_DETECT_DEVICES ]
        return self._loop.run_until_complete(self.write_await_callback(self.SENSOR_SERVICE_ID, cmd))


    def initialize_device(self):
        """
        Parse datasheets.py to get the data on all channels (characteristics) on the interface
        """
        try:
            interface = self._xml_root.find("./Interfaces/Interface[@ID='%s']" % self._interface_id)

            self._device_channels = [
                {
                    'id': int(c.get('ID')),
                    'name': c.get('NameTag'),
                    'sensor_id': int(c.get('SensorID')) if 'SensorID' in c.attrib else 0,
                    'type': c.get('Type'),
                    'output_type': c.get('OutputType') if 'OutputType' in c.attrib else '',
                    'measurements': [],
                    'total_data_size': 0,
                    'plug_detect': int(c.get('PlugDetect')) if 'PlugDetect' in c.attrib else 0,
                    'channel_id_tag': c.get('ChannelIDTag') if 'ChannelIDTag' in c.attrib else '',
                    'factory_cal_ids': []
                }
                for c in interface.findall("./Channel")
            ]

            # If it is possible to plug a sensor into the device, then check if there is one plugged in
            if any([device['plug_detect'] == 1 for device in self._device_channels]):
                self.scan_controlnode_plugins()

            else:
                self.initialize_device_sensors()
        
        except:
            raise self.SensorSetupError
        

    def initialize_device_sensors(self, plugin_sensor_ids = None):
        try:
            # FOR DEVICES WITH PLUGIN SENSORS (e.g. controlnode)
            # on callback from the "send plugin sensors" command change the appropriate
            # device channel's sensor_id to the ID returned for that channel in the callback.
            # if no sensor ID is returned for that channel in the callback, then set sensor_id to ''
            # Here I am assuming that the IDs in the callback are returned in sequential order of their channels
            # (they are for the control node)
            if plugin_sensor_ids != None:
                i = 0
                for channel in self._device_channels:
                    if channel['plug_detect']:
                        channel['sensor_id'] = plugin_sensor_ids[i]
                        i += 1

            # Iterate over channels on the interface
            for channel in self._device_channels:
                # if the interface channel is for a sensor then initialize it
                if channel['type'] == 'Pasport' and channel['sensor_id'] != 0:
                    self._initialize_sensor(channel)
   

            # Initialize device measurement values
            # If the device channel has measurements (i.e. is a sensor channel) then associate that measurement with its channel ID
            self._measurement_sensor_ids = { measurement: channel['id'] for channel in self._device_channels for measurement in channel['measurements'] }
            self._data_results = { m: None for sensor in self._device_channels for m in sensor['measurements'] }
            self._sensor_names = {sensor['name'] : sensor for sensor in self._device_channels}

        except:
            raise self.SensorSetupError
        
    def _not_internal(self, measurement: dict) -> bool:
        """
        Check if a measurement is internal so that we don't display it to the user
        Args:
            measurement (dict): the measurement data from datasheets.py
        """
        measurement_attributes = measurement.attrib
        if 'Internal' in measurement_attributes.keys():
            if measurement_attributes['Internal']=='1':
                return False
        elif 'InternalUnit' in measurement_attributes.keys():
            return False
        else:
            return True
        
    def _not_derivative(self, measurement:dict) -> bool:
        """
        Check if a measurement is a derivative so we don't show it to the user
        Args: 
            measurement (dict): the measurement data from datasheets.py
        """
        return measurement.get("Type") != "Derivative"
    
    
    def _initialize_sensor(self, sensor_channel):
        """
        Parse the datasheet to initialize a sensor with its measurements and their attributes
        Args:
            sensor_channel (dict): the sensor channel we are filling in data for
        """
        # initialize attributes associated with the channel
        self._data_ack_counter[sensor_channel['id']] = 0
        self._data_stack[sensor_channel['id']] = []
        self._device_measurements[sensor_channel['id']] = {}

        # get sensor data associated with that channel
        sensor_data = self._xml_root.find("./Sensors/Sensor[@ID='%s']" % sensor_channel['sensor_id'])

        # get name of sensor (e.g. "ControlNodeAcceleration")
        sensor_channel['name'] = sensor_data.get('Tag')
        # put names of non-internal measurements provided by sensor (e.g. "RawX, Accelerationy") into the sensor channel
        sensor_channel['measurements'] = [m.get('NameTag') for m in sensor_data.findall("./Measurement") if self._not_internal(m) and self._not_derivative(m)]
        # get factory calibration IDs
        sensor_channel['factory_cal_ids'] = [m.get('ID') for m in sensor_data.findall("./Measurement[@Type='FactoryCal']")]

        # collect attributes of all measurements that the sensor can take
        for measurement in sensor_data.findall("./Measurement"):
            # add a dictionary connecting the measurement ID with a dictionary of all its attributes
            measurement_id = {int(measurement.get('ID')): measurement.attrib}
            self._device_measurements[sensor_channel['id']].update(measurement_id)

        # fix types of measurement attributes so they are usable
        for sensor_m_id, sensor_m in self._device_measurements[sensor_channel['id']].items():
            sensor_m['ID'] = int(sensor_m['ID'])
            sensor_m['Type'] = sensor_m['Type'] if 'Type' in sensor_m else ''
            sensor_m['Visible'] = int(sensor_m['Visible']) if 'Visible' in sensor_m else 0
            sensor_m['Internal'] = int(sensor_m['Internal']) if 'Internal' in sensor_m else 0
            if 'DataSize' in sensor_m:
                sensor_m['DataSize'] = int(sensor_m['DataSize'])
                sensor_channel['total_data_size'] += sensor_m['DataSize']
            if 'Inputs' in sensor_m and str(sensor_m['Inputs']).isnumeric(): sensor_m['Inputs'] = int(sensor_m['Inputs'])
            if 'Precision' in sensor_m and str(sensor_m['Precision']).isnumeric(): sensor_m['Precision'] = int(sensor_m['Precision'])
            #TODO: This is a temporary workaround for the code node cart
            if sensor_m['NameTag'] == "RawCartPosition":
                sensor_m['DataSize'] = 0
            sensor_m['Value'] = sensor_m['Value'] if 'Value' in sensor_m else 0 if sensor_m['Type'] == 'RotaryPos' else None


        # if you connect two of the same sensor (such as two high speed steppers)
        # then after the xml finishes reading for the first it will be gone and unavailable to initialize the second
        # thus if there is no sensor data for measurements we copy the data from the initialized sensor
        if len(sensor_channel['measurements']) == 0:
            for initialized_channel in [ch for ch in self._device_channels if ch['measurements'] != []]:
                if initialized_channel['sensor_id'] == sensor_channel['sensor_id']:
                    sensor_channel['measurements'] = initialized_channel['measurements']
        
        # Initialize internal sensor measurement values
        self._sensor_data[sensor_channel['id']] = { m_id: m['Value'] for m_id, m in self._device_measurements[sensor_channel['id']].items() }
       
        # TODO: Factory Calibration check
        # self.read_factory_cal(sensor_channel['id'])
        return



    def get_sensor_list(self):
        """
        Return list of sensor names that a device has
        """
        if self.is_connected() is False:
            raise self.DeviceNotConnected()

        return [sensor_name for sensor_name, sensor in self._sensor_names.items()]


    def get_measurement_list(self, sensor_name=None):
        """
        Return list of measurements that a device can read

        Args:
            sensor_name (string, optional): Sensor to return measurements for
        """
        if self.is_connected() is False:
            raise self.DeviceNotConnected()

        if sensor_name and type(sensor_name) is not str:
            raise self.InvalidParameter

        if sensor_name == None:
            measurement_list = []
            for sensor_measures in [sensor['measurements'] for sensor in self._device_channels]:
                for measure in sensor_measures:
                    measurement_list.append(measure)
                    
        elif sensor_name in self._sensor_names:
            measurement_list = self._sensor_names[sensor_name]['measurements']
        else:
            raise self.SensorNotFound

        return measurement_list


    def read_factory_cal(self, sensor_id):
        """
        Read factory calibrations from sensor's built in memory
        """
        factory_cal_count = 0

        for m_id, m in self._device_measurements[sensor_id].items():
            if m['Type'] == 'FactoryCal':
                m['FactoryCalOrder'] = factory_cal_count
                factory_cal_count += 1

        if factory_cal_count > 0:
            # Transfer Block RAM Command
            ll_read = 128
            ll_storage = 3
            ll = ll_read + ll_storage

            address = sensor_id + 2
            num_bytes = 16 * factory_cal_count
            service_id = self.SENSOR_SERVICE_ID
            
            command = [ self.GCMD_XFER_BURST_RAM, ll,
                        address & 0xFF, address>>8 & 0XFF, address>>16 & 0XFF, address>>24 & 0XFF,
                        num_bytes & 0xFF, num_bytes>>8 & 0XFF ]

            self._loop.run_until_complete(self.write_await_callback(service_id, command))

            #Start Block Command
            command = [ 0X09, 0X01, num_bytes & 0XFF, num_bytes>>8 & 0XFF, 16 ]

            self._loop.run_until_complete(self.write_await_callback(service_id, command))

            """
            for m_id, m in self._device_measurements[sensor_id].items():
                i = 0
                if m['Type'] == 'FactoryCal':
                    m['FactoryCalParams'] = self._factory_cal_params[i]
            
            self._factory_cal_params = {}
            """


# ---------- Communicating ----------


    def _send_ack(self, service_id, command):
        """
        Write acknowledgement packet to sensor for continuous data

        Args:
            service id (int): Sensor channel we are sending data to
            command (bytearray): Bytes array that contains the packet number we last received
        """
        uuid = self._set_uuid(service_id, self.SEND_ACK_CHAR_ID)

        try:
            self._loop.run_until_complete(self.write(uuid, command))
        except:
            raise self.CommunicationError


    async def write(self, service_id, command):
        """
        Write to the device
        Args:
            service_id (int): characteristic we are writing to
            command (bytes): the command to send
        """
        #data_to_write = bytes(command).hex()
        #ble_write_data = f'WRITE# {data_to_write} to {uuid}'
        #print(ble_write_data)

        uuid = self._set_uuid(service_id, self.SEND_CMD_CHAR_ID)
        try:
            await self._client.write_gatt_char(uuid, bytes(command))
        except:
            raise self.CommunicationError


    def _set_device_params(self, ble_device):
        """
        Get the device name and sensor ID from the BLE advertised name

        Args:
            ble_device (BLEDevice): The user selected BLE device
        """
        self._address = ble_device.address
        name_parts = ble_device.name.rsplit(' ', 1)
        self._dev_type = name_parts[0]
        self._serial_id = name_parts[1][0:7]
        self._name = self._dev_type + ' ' + self._serial_id
        self._interface_id = self._decode64(name_parts[1][8]) + 1024


    def process_measurement_response(self, sensor_id, data):
        # Received periodic data
            if (data[0] <= 0x1F):
                # Add data to stack
                self._data_stack[sensor_id] += data[1:]
                self._data_ack_counter[sensor_id] += 1
                self._loop.create_task(self._decode_data(sensor_id))
                # Send acknowledgement package
                if (self._data_ack_counter[sensor_id] > 8):
                    try:
                        self._data_ack_counter[sensor_id] = 0
                        service_id = sensor_id + 1
                        command = [ data[0] ]
                        self._send_ack(service_id, command)
                    except:
                        raise self.CommunicationError()
                    
                return
            
            elif data[0] is self.CNTRLNODE_PLUGINS_CALLBACK:
                
                self.update_controlnode_plugin_sensor(data)
                

            # Received single data packet
            elif (data[0] is self.GRSP_RESULT):
                # Valid data 
                if data[1] == 0x00:
                    if data[2] is self.GCMD_READ_ONE_SAMPLE: # Get single measurement packet
                        self._data_packet = data[3:]
                        
                    elif data[2] == 1: #SPI Data (ex: AirLink Interface connected)
                        pasport_service_id = 1
                        self._loop.run_until_complete(self.write_await_callback(pasport_service_id, [ 0x08 ]))
                        # self._loop.run_until_complete(self._single_listen(pasport_service_id))
                        #TODO: AirLink things

                # Error receiving data
                elif data[1] == 0x01:
                    pass

            elif (data[0] == self.GEVT_SENSOR_ID):
                self._airlink_sensor_id = data[1]


    def update_controlnode_plugin_sensor(self, data):
        """
        Parse data about the plugin sensors in response to a plugin sensor update callback
        from the control node. 
        """
        # using the struct module, unpack the data via a little-endian encoding
        # see https://docs.python.org/3/library/struct.html
        sensor_ids = struct.unpack('<xhhh', data)
        self.initialize_device_sensors(sensor_ids)
        pass


    def process_device_response(self, data):
        # Received single data packet
        self._response_data = data
        if (data[0] is self.GRSP_RESULT):
            # Valid data 
            if data[1] == 0x00:
                # Get single measurement packet
                # the self.GCMD_CONTROL_NODE_CMD allows get_stepper_remaining to work
                if data[2] is self.GCMD_READ_ONE_SAMPLE or self.GCMD_CONTROL_NODE_CMD:
                    self._data_packet = data[3:]
                    

        # TODO: Get factory calibration
        elif (data[0] == 0x0A):
            self._factory_calibrate(data)

        elif (data[0] == 0x0B):
            self._notify_sensor_id = None



    def _factory_calibrate(self, data):
        factory_cal_params = {data[1]: []}
        #self._factory_cal_params[data[1]] = []
        num_params = 4
        byte_len = 4
        cal_data = data[2:]
        for p in range(num_params):
            byte_value = 0
            for d in range(byte_len):
                stack_value = cal_data.pop(0)
                byte_value += stack_value * (2**(8*d))

            param = self._binary_float(byte_value, byte_len)
            factory_cal_params[data[1]].append(param)

        # Save factory calibration parameters to measurement
        for m_id, m in self._device_measurements[self._notify_sensor_id].items():
            if 'FactoryCalOrder' in m and m['FactoryCalOrder'] in factory_cal_params:
                m['FactoryCalParams'] = factory_cal_params[m['FactoryCalOrder']]


    async def _notify_callback(self, bleakGATTChar: BleakGATTCharacteristic, data: bytearray):
        """
        Handle all callbacks from the device. The link between the characteristics who send callbacks
        and this function was made by start_notify() in _async_connect()
        
        """
        handle = bleakGATTChar.handle
        # check that we're getting a valid callback, not just a battery status update
        if data[0] in [0xC0, 0x82]:
            # place the callback in the queue so we can synchronize off of it
            await self._queue.put(True)

        # Reading measurement response
        if self._handle_service[handle] > 0:
            sensor_id = self._handle_service[handle] - 1
            self.process_measurement_response(sensor_id, data)
            

        # Reading device response
        elif self._handle_service[handle] == self.SENSOR_SERVICE_ID:
            self.process_device_response(data)
            

    async def check_callback(self):
        # checks for a callback from the _notify_callback() function
        await self._queue.get()
        self._queue.task_done()


    async def write_await_callback(self, service_id, one_shot_cmd):
        """
        This function bundles writing and listening for a callback into a TaskGroup
        forcing execution to stop until it receives the callback, synchronizing communication.
        """
        # sends a write command requesting data and listens until it gets the callback notification
        async with asyncio.TaskGroup() as tg:
            write = tg.create_task(self.write(service_id, one_shot_cmd))
            check_done = tg.create_task(self.check_callback())

     

# ---------- Reading data --------

    def read_data(self, measurement):
        """
        Read a sensor measurement

        Args:
            measurement (string): name of measurement we want to read
        """

        if self.is_connected() is False:
            raise self.DeviceNotConnected()

        if measurement == None or type(measurement) is not str:
            raise self.InvalidParameter
        else:
            try:
                sensor_id = self._measurement_sensor_ids[measurement]
            except:
                raise self.MeasurementNotFound
            
            self._get_sensor_measurements(sensor_id)


            return self._data_results[measurement]


    def read_data_list(self, measurements):
        """
        Read multiple sensor measurements

        Args:
            measurement (list[string]): List of measurements that we want to read
        """
        if self.is_connected() is False:
            raise self.DeviceNotConnected()

        if measurements == None or type(measurements) is not list:
            raise self.InvalidParameter
        for m in measurements:
            if type(m) is not str:
                raise self.InvalidParameter
        else:
            try:
                sensor_ids = {self._measurement_sensor_ids[m] for m in measurements}
            except:
                raise self.MeasurementNotFound

            try:
                for sensor_id in sensor_ids:
                    self._get_sensor_measurements(sensor_id)
                    
                measurement_data = {}
                for measurement in measurements:
                    measurement_data[measurement] = self._data_results[measurement]

                return measurement_data

            except:
                raise self.InvalidParameter


    def get_measurement_unit(self, measurement):
        """
        Return a measurement's default units

        Args:
            measurement (string): name of measurement we want the units for
        """

        if self.is_connected() is False:
            raise self.DeviceNotConnected()

        if measurement == None or type(measurement) is not str:
            raise self.InvalidParameter
        else:
            try:
                sensor_id = self._measurement_sensor_ids[measurement]
                for m_id, m in self._device_measurements[sensor_id].items():
                    if m['NameTag'] == measurement:
                        return m['UnitType']
            except:
                raise self.InvalidParameter

        return None

            
    def get_measurement_unit_list(self, measurements):
        """
        Return default units for multiple measurements

        Args:
            measurements (list[string]): List of measurements that we want the units for
        """

        if self.is_connected() is False:
            raise self.DeviceNotConnected()

        if measurements == None or type(measurements) is not list:
            raise self.InvalidParameter    
        else:
            try:
                sensor_ids = {self._measurement_sensor_ids[m] for m in measurements}

                measurement_units = {
                    measurement: m['UnitType']
                    for sensor_id in sensor_ids
                    for m_id, m in self._device_measurements[sensor_id].items()
                    for measurement in measurements
                    if m['NameTag'] == measurement
                }
                return measurement_units
            except:
                raise self.InvalidParameter

        return None
    
    def _request_sensor_data(self, sensor_id):
        service_id = sensor_id + 1

        for sensor in self._device_channels:
            if sensor['id'] == sensor_id:
                packet_size = sensor['total_data_size']

        one_shot_cmd = [ self.GCMD_READ_ONE_SAMPLE, packet_size ]

        self._loop.run_until_complete(self.write_await_callback(service_id, one_shot_cmd))


    def _get_sensor_measurements(self, sensor_id):
        # request data
        self._request_sensor_data(sensor_id)
        # process the data
        self._data_stack[sensor_id] = self._data_packet
        self._decode_data(sensor_id)


# ---------- Processing ----------


    def _decode64(self, charVal):
        """
        Decode Base-64 character to corresponding integer
        0-9 	-> '0' - '9'
        10-25	-> 'K' - 'Z'
        26-35	-> 'A' - 'J'
        36-61	-> 'a' - 'z'
        62		-> '#'
        63		-> '*'

        Args:
            charVal (char): A single character

        Returns:
            Integer value corresponding to the Base-64 character
        """
        if charVal >= '0' and charVal <= '9':
            return ord(charVal) - ord('0')
        elif charVal >= 'K' and charVal <= 'Z':
            return ord(charVal) - ord('A')
        elif charVal >= 'A' and charVal <= 'J':
            return ord(charVal) - ord('A') + 26
        elif charVal >= 'a' and charVal <= 'z':
            return ord(charVal) - ord('a') + 36
        elif charVal == '*':
            return 62
        elif charVal == '#':
            return 63
        else:
            return -1


    def _twos_comp(self, value, byte_len):
        """
        Get two's complement of an integer value

        Args:
            value (int): Integer value we want to convert
            byteLength (int): Number of bytes the integer is supposed to be

        Returns:
            Two' complement of an integer value
        """
        bit_len = byte_len * 8
        if value and value > (1<<(bit_len-1)):
            return value-(1<<bit_len)
        return value


    def _binary_fraction(self, value):
        return (value >> 16) + ((value & 0xFFFF)/2**16)


    def _binary_float(self, value, byte_len):
        """ IEEE 754 Conversion"""
        bit_len = byte_len * 8
        sign = 1 if value >> 31 == 0 else -1
        exp = (value >> (bit_len-9)) & 0xFF
        mantissa = value & 0xFFFFFF | 0x800000 if exp != 0 else value & 0x7FFFFFFF

        return float(sign * mantissa * 2**(exp-150))


    def _calc_4_params(self, raw, x1, y1, x2, y2):
        # This does slope offset according to the factory calibration
        b = (x1*y2 - x2*y1)/(x1-x2)
        if (x1 != 0):
            m = (y1 - b)/x1
        if (x2 != 0):
            m = (y2 - b)/x2
        
        return m * raw + b


    def _limit(self, num, minimum, maximum):
        """
        Limits input number between minimum and maximum values.

        Args:
            num (int/float): input number
            minimum (int): min number
            maximum (int): max number
        """
        return max(min(num, maximum), minimum)


    def _calc_linear_params(self, raw, m, b):
        """
        Return corresponding value of an input using a basic linear equation

        Args:
            raw (float): Linear equation "x" value
            m (float): Slope
            b (float): y-intercept
        """
        return m * raw + b


    def _calc_rotary_pos(self, count, x, r):
        return (count * x) / r

    
    def _decode_auto_id_packet(self, sensor_id):

        plug_count = 0
        for sensor in self._device_channels:
            if sensor['plug_detect'] == 1:
                plug_count += 1

        results = []

        
        if len(self._data_stack[sensor_id]):
            for i in range(plug_count):
                byte_value = 0
                for d in range(2):
                    #if len(self._data_stack[sensor_id]):
                    stack_value = self._data_stack[sensor_id].pop(0)
                    byte_value += stack_value * (2**(8*d))
                results.append(byte_value)
        
        return results


    def _decode_data(self, sensor_id):
        try:
            self._sensor_data_prev[sensor_id] = self._sensor_data[sensor_id].copy()
            # self._sensor_data[sensor_id] = { m_id: m['Value'] for m_id, m in self._device_measurements[sensor_id].items() }

            for m_id, raw_m in self._device_measurements[sensor_id].items():
                result_value = None
                if raw_m['Type'] == 'RawDigital':
                    byte_value = 0
                    for d in range(raw_m['DataSize']):
                        if len(self._data_stack[sensor_id]):
                            stack_value = self._data_stack[sensor_id].pop(0)
                            byte_value += stack_value * (2**(8*d))
                            result_value = byte_value
                    if (raw_m['DataSize'] == 4 or ('TwosComp' in raw_m and int(raw_m['TwosComp']) == 1)):
                        result_value = self._twos_comp(result_value, raw_m['DataSize'])

                elif raw_m['Type'] == 'Direct':
                    byte_value = 0
                    for d in range(raw_m['DataSize']):
                        if len(self._data_stack[sensor_id]):
                            stack_value = self._data_stack[sensor_id].pop(0)
                            byte_value += stack_value * (2**(8*d))

                    if raw_m['DataSize'] == 4:
                        byte_value = self._twos_comp(byte_value, raw_m['DataSize'])
                        result_value = float(self._binary_fraction(byte_value))
                    
                    result_value = round(result_value, raw_m['Precision']) if 'Precision' in raw_m else result_value

                elif raw_m['Type'] == 'Constant':
                    result_value = float(raw_m['Value'])
                    result_value = round(result_value, raw_m['Precision']) if 'Precision' in raw_m else result_value

                val = {raw_m['ID']: result_value}
                self._sensor_data[sensor_id].update(val)

            # This calculates every measurement available at the sensor, not just the measurement requested.
            # Every time you ping a sensor it updates all measurements available from that sensor.
            # It has to do this because many measurements are derived from others (i.e. VWCLoam derived from RawMoisture)
            for m_id, m in self._device_measurements[sensor_id].items():
                if self._sensor_data[sensor_id][m_id] == None:
                    result_value = self._get_measurement_value(sensor_id, m_id)
                    if 'Precision' in m and result_value != None:
                        result_value = round(result_value, m['Precision'])

                    if 'Limits' in m and result_value != None:
                        limits = [int(lim) for lim in m['Limits'].split(',')]
                        result_value = self._limit(result_value, limits[0], limits[1])

                    val = {m_id: result_value}
                    self._sensor_data[sensor_id].update(val)

            # Set visible data variables
            try:
                for sensor_id, measurements in self._device_measurements.items():
                    for m_id, m in measurements.items():
                        if (m['Visible'] == 1 and self._sensor_data[sensor_id][m_id] != None):
                            result_val = { m['NameTag']: self._sensor_data[sensor_id][m_id] }
                            self._data_results.update(result_val)
            except:
                raise self.SensorSetupError

        except:
            raise self.CouldNotDecodeData


    def _get_measurement_value(self, sensor_id, measurement_id):
        """
        Now that we have the measurement values for the sensor, 
        calculate a user-readable data value as outlined in the datasheet. 
        """
        m = self._device_measurements[sensor_id][measurement_id]

        result_value = None

        if m['Type'] == 'RawDigital' and self._sensor_data[sensor_id][measurement_id] == None:
            pass

        if 'Inputs' in m:
            result_value = self._calculate_with_input(m, sensor_id)

        if ('Equation' in m):
            result_value = self._calculate_with_equation(m, sensor_id)

        return result_value
    
    def _calculate_with_input(self, m, sensor_id):
        """
        Calculate measurement value for a measurement that has an input parameter
        Args:
            m (dict): measurement attributes
            sensor_id (int): id of sensor from which we got the measurement
        """
        # Multiple Input
        if m['Type'] == 'ThreeInputVector':
            inputs = m['Inputs'].split(',')
            missing_param = False
            for input in inputs:
                if self._sensor_data[sensor_id][int(input)] is None:
                    missing_param = True
                    break
            if missing_param is False:
                ax = self._sensor_data[sensor_id][int(inputs[0])]
                ay = self._sensor_data[sensor_id][int(inputs[1])]
                az = self._sensor_data[sensor_id][int(inputs[2])]
                return math.sqrt(ax**2 + ay**2 + az**2)
        elif m['Type'] == 'Select': # For Current, Voltage and Accel
            inputs = m['Inputs'].split(',')

            need_input = int(inputs[0])

            if self._sensor_data[sensor_id][need_input] is not None:
                return self._sensor_data[sensor_id][need_input]
            else:
                return self._get_measurement_value(sensor_id, need_input)

        # Single Input
        else:
            need_input = int(m['Inputs'])
            input_value = None

            if self._sensor_data[sensor_id][need_input] is not None:
                input_value = self._sensor_data[sensor_id][need_input]
            else:
                input_value = self._get_measurement_value(sensor_id, need_input)

            if (input_value is not None):
                if m['Type'] == 'UserCal':
                    params = m['Params'].split(',')
                    return self._calc_4_params(input_value, float(params[0]), float(params[1]), float(params[2]), float(params[3]))

                elif m['Type'] == 'FactoryCal':
                    if 'FactoryCalParams' in m and len(m['FactoryCalParams']) == 4:
                        params = m['FactoryCalParams']
                    else:
                        params = m['Params'].split(',')
                    return self._calc_4_params(input_value, float(params[0]), float(params[1]), float(params[2]), float(params[3]))

                elif m['Type'] == 'LinearConv':
                    params = m['Params'].split(',')
                    return self._calc_linear_params(input_value, float(params[0]), float(params[1]))

                elif m['Type'] == 'Derivative':
                    if self._sensor_data_prev[sensor_id][m['Inputs']] != None:
                        prev_input_value = self._sensor_data_prev[sensor_id][m['Inputs']]
                        return (input_value - prev_input_value) / 2

                elif m['Type'] == 'RotaryPos':
                    params = m['Params'].split(',')
                    m['Value'] += self._calc_rotary_pos(input_value, float(params[0]), float(params[1]))
                    return m['Value']
    
    def _calculate_with_equation(self, m, sensor_id):
        """
        Calculate measurement value for a measurement that has a calculation parameter in the datasheet
        Args:
            m (dict): measurement attributes
            sensor_id (int): id of sensor from which we got the measurement
        """
        raw_equation = m['Equation']

        eqn_variables = re.findall(r"\[([0-9_]+)\]", raw_equation)

        for eVar in eqn_variables:
            bracket_val = '[' + eVar + ']'
            eVarKey = int(eVar)

            raw_equation = raw_equation.replace('^', '**')

            # replace the reference to a value in the callback with its value
            if self._sensor_data[sensor_id][eVarKey] != None:
                replace_with = str(self._sensor_data[sensor_id][eVarKey])
                raw_equation = raw_equation.replace(bracket_val, replace_with)
            else:
                replace_with = str(self._get_measurement_value(sensor_id, eVarKey))
                raw_equation = raw_equation.replace(bracket_val, replace_with)


        if raw_equation.startswith('table'):
            return self._equation_eval_table(raw_equation)

        # organize the equation by parentheses. 
        paranthetic_vals = list(self.parenthetic_contents(raw_equation))

        for i, eqn in paranthetic_vals:
            if (eqn.startswith('limit')):
                limit_eqn = eqn.replace('limit(','')
                limit_eqn = limit_eqn.replace(')','')
                limit_vals = limit_eqn.split(',')
                val = float(limit_vals[0])
                min_val = float(limit_vals[1])
                max_val = float(limit_vals[2])
                
                if (val < min_val):
                    val = min_val
                elif (val > max_val):
                    val = max_val
    
                raw_equation = raw_equation.replace(eqn, str(val))
            
            # TODO: Bring other equations into here

        if raw_equation.startswith('usound'):
            usound_eqn = raw_equation.replace('usound(','')
            usound_eqn = usound_eqn.replace(')','')
            usound_vals = usound_eqn.split(',')

            ping_echo_time = float(usound_vals[0])
            speed_of_sound = float(usound_vals[1])

            return (ping_echo_time/1000000) * speed_of_sound / 2 # result in meters

        elif raw_equation.startswith('dewpoint'):
            dewpoint_eqn = raw_equation.replace('dewpoint(','')
            dewpoint_eqn = dewpoint_eqn.replace(')','')
            dewpoint_vals = dewpoint_eqn.split(',')

            if (dewpoint_vals[0] != 'None'):
                temp_c = float(dewpoint_vals[0])
                relative_humidity = float(dewpoint_vals[1])
                vapor_pressure_sat = 6.11 * pow( 10, (7.5 * temp_c) / (237.7 + temp_c) )
                vapor_pressure_actual = (relative_humidity * vapor_pressure_sat) / 100

                return (-443.22 + 237.7 * math.log(vapor_pressure_actual)) / (-math.log(vapor_pressure_actual) + 19.08)

        elif raw_equation.startswith('windchill'):
            windchill_eqn = raw_equation.replace('windchill(','')
            windchill_eqn = windchill_eqn.replace(')','')
            windchill_vals = windchill_eqn.split(',')

            if windchill_vals[0] != 'None' and windchill_vals[1] != 'None':
                temp_f = (9 * float(windchill_vals[0]) / 5) + 32
                wind_mph = float(windchill_vals[1]) * 2.237

                if( wind_mph < 3.0 or temp_f > 50.0 ):
                    wind_chill_f = temp_f
                else:
                    wind_chill_f = 35.74 + 0.6215 * temp_f - 35.75 * pow( wind_mph, 0.16 ) + 0.4275 * temp_f * pow( wind_mph, 0.16 )

                return 5 * (wind_chill_f - 32) / 9
        
        elif raw_equation.startswith('heatindex'):
            heatindex_eqn = raw_equation.replace('heatindex(','')
            heatindex_eqn = heatindex_eqn.replace(')','')
            heatindex_vals = heatindex_eqn.split(',')

            temp_c = float(heatindex_vals[0])
            relative_humidity = float(heatindex_vals[1])
            vapor_pressure_sat = 6.11 * pow( 10, (7.5 * temp_c) / (237.7 + temp_c) )
            vapor_pressure_actual = (relative_humidity * vapor_pressure_sat) / 100

            return temp_c + 0.55555 * (vapor_pressure_actual - 10.0)

        elif raw_equation.startswith('codenodepos'):
            None

        else:
            try:
                raw_equation = raw_equation.replace('sqrt', 'math.sqrt')
                raw_equation = raw_equation.replace('atan2', 'math.atan2')
                raw_equation = raw_equation.replace('log', 'math.log10')

                if "None" in raw_equation:
                    return None
                else:
                    return eval(raw_equation)

            except:
                # equation likely has a string that we don't recognize yet
                raise self.InvalidEquation("Error decoding the raw data")

    def _equation_eval_table(self, raw_equation: str) -> float:
        """
        args:
            raw_equation (str): equation string to evaluate as a table using linear interpolation

        Evaluates an equation string to return a measurement value
        Many measurements on the datasheet have equations that involve tables.
        These tables contain an x value at the beginning and a series of points to use for linear interpolation
        This function steps in once the variable is determined. It evaluates x, does linear interpolation, and returns y
        raw_equation looks like this: "table((880*60.8)+336.9,7122,45,14100,20,17245,15,51725,0)"
        """
        trimmed_equation = raw_equation[6:-1]
        elements = trimmed_equation.split(',')
        # grab just the expression pertaining to x and evaluate it
        x = eval(elements.pop(0))
        # now put the remaining values into a list as tuples of 2 (representing points)
        elements = [float(e) for e in elements]
        points = []
        while(len(elements)>0):
            points.append(tuple(elements[0:2]))
            elements = elements[2:]

        result = self.linear_interpolate(x, points)
        return result
    
    def linear_interpolate(self, x: float, points: list[tuple]) -> float:
        for i in range(len(points) - 1):
            xi, yi = points[i]
            x_next, y_next = points[i + 1]

            if xi <= x <= x_next:
                break
        
        # deal with x outside the range of points
        if x < points[0][0]:
            xi, yi = points[0]
            x_next, y_next = points[1]
        elif x > points[-1][0]:
            xi, yi = points[-2]
            x_next, y_next = points[-1]

        return (y_next - yi)/(x_next - xi) * (x - xi) + yi


    def parenthetic_contents(self, string):
        """Generate parenthesized contents in string as pairs (level, contents)."""
        stack = []
        for i, c in enumerate(string):
            if c == '(':
                stack.append(i)
            elif c == ')' and stack:
                start = stack.pop()
                yield (len(stack), string[start + 1: i])


    class Error(Exception):
        """Base class for other exceptions"""
        pass
    
    class BLEScanFailed(Exception):
        """Error occured when trying to scan for a BLE sensor"""
        pass

    class BLEConnectionError(Exception):
        """Raised when there was error connecting to the device"""

    class BLEAlreadyConnectedError(Exception):
        """Raised when the input value is too large"""
        pass

    class DeviceNotConnected(Exception):
        """Raised when there is no device connected"""
        pass

    class MeasurementNotFound(Exception):
        """Raised when a requested measurement does not belong to a device"""
        pass

    class InvalidParameter(Exception):
        """An invalid parameter was passed in"""
        pass

    class SensorNotFound(Exception):
        """The device does not have this sensor"""
        pass

    class InvalidEquation(Exception):
        """Could not calculate the measurement"""
        pass

    class CouldNotDecodeData(Exception):
        """Could not decode data the raw data from the sensor"""
        pass

    class CommunicationError(Exception):
        """Error sending or receiving data from the sensor"""
        pass

    class SensorSetupError(Exception):
        """Error setting the sensor parameters up"""
        pass


def main():
    my_sensor = PASCOBLEDevice()
    found_devices = my_sensor.scan()

    print('\nDevices Found')
    for _, ble_device in enumerate(found_devices):
        display_name = ble_device.name.split('>')
        print(f'{_}: {display_name[0]}')

    # Auto connect if only one sensor found
    selected_device = input('Select a device: ') if len(found_devices) > 1 else 0
    ble_device = found_devices[int(selected_device)]

    my_sensor.connect(ble_device)
    
    #my_sensor.TIME_DELAY = 5
    measurements = (my_sensor.get_measurement_list())

    for i in range(100):
        for m in measurements:
            print(f'{m} : {my_sensor.read_data(m)}')

    my_sensor.disconnect()


if __name__ == "__main__":
    main()
