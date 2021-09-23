import asyncio
import math
import os
import re
import time
import xml.etree.ElementTree as ET

from bleak import BleakClient, discover
from bleak.backends.device import BLEDevice
from uuid import UUID


class PASCOBLEDevice():
    """
    PASCO Device object that has functions for connecting and getting data
    """

    SENSOR_SERVICE_ID = 0

    SEND_CMD_CHAR_ID = 2
    RECV_CMD_CHAR_ID = 3
    SEND_ACK_CHAR_ID = 5

    GCMD_READ_ONE_SAMPLE = 0x05
    GCMD_XFER_BURST_RAM = 0X0E

    GRSP_RESULT = 0XC0                      # Generic response packet
    GEVT_SENSOR_ID = 0x82                   # Get Sensor ID (for AirLink)


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
        self._loop = asyncio.get_event_loop()
        self._data_ack_counter = {}

        self._device_sensors = []
        self._device_measurements = []
        self._handle_service = {}
        self._data_stack = {}
        self._single_measurement_packet = []
        self._sensor_measurements = {}
        self._factory_cal_params = {}
        self._sensor_data = {}
        self._sensor_data_prev = {}
        self._dropcount = 0

        self._data_results = {}
        self._measurement_sensor_ids = {}

        # Load Datasheet
        package_path = os.path.dirname(os.path.abspath(__file__))
        datasheet_path = os.path.join(package_path, 'datasheets.xml')
        tree = ET.parse(datasheet_path)
        self._xml_root = tree.getroot()

        self._compatible_devices = [
            'Accel Alt',
            'Optical DO',
            'Drop Counter',
            'O2',
            'Temperature',
            'Mag Field',
            'Rotary Motion',
            'Motion',
            'Weather',
            'CO2',
            'Smart Cart',
            'pH',
            'Light',
            'Force Accel',
            'Pressure',
            'Conductivity',
            'Voltage',
            'Current',
            'BP',
            'Load Cell',
            'Diffraction',
            '//code.Node',
        ]
        """
        self._not_compatible_devices = [
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
    def loop(self):
        return self._loop

    @property
    def address(self):
        return self._address

    @property
    def data_results(self):
        return self._data_results

    @property
    def device_sensors(self):
        return self._device_sensors

    @property
    def measurement_sensor_ids(self):
        return self._measurement_sensor_ids


    def scan(self, sensor_name_filter=None):
        """
        Scans for all PASCO devices

        Args:
            sensor_name_filter (string): Sensor name to scan for

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
        found_devices = []
        
        bleak_devices = await discover() #returns array of all devices found via bluetooth scan

        for ble_device in bleak_devices:
            for pasco_device_name in pasco_device_names:
                if pasco_device_name in ble_device.name and ble_device not in found_devices:
                    found_devices.append(ble_device)

        return found_devices


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


    def connect(self, ble_device: BLEDevice):
        """
        Connect to a bluetooth device

        Args:
            ble_device (BLEDevice): Device object discovered up when doing scan
        """
    
        if self._client is None:
            self._client = BleakClient(ble_device.address)

            try:
                self._loop.run_until_complete(self._async_connect())
                self.keepalive()
            except ConnectionError:
                exit(1)
            else:
                self._set_device_params(ble_device)
                self._loop.run_until_complete(self._initialize_sensor_values())
        else:
            raise self.BLEAlreadyConnectedError()



    def connect_by_id(self, pasco_device_id):
        """
        Connect to a bluetooth device

        Args:
            pasco_device_id (string): Device's 6 digit ID (with dash)
        """
    
        if self._client is None:
            found_devices = self.scan(pasco_device_id)
            ble_device = found_devices[0]

            self.connect(ble_device)
        else:
            raise self.BLEAlreadyConnectedError()


    async def _async_connect(self):
        await self._client.connect()
        if not self._client.is_connected:
            return False

        self._set_handle_service()

        uuid = self._set_uuid(self.SENSOR_SERVICE_ID, self.RECV_CMD_CHAR_ID)
        await self._client.start_notify(uuid, self._notify_callback)


    def keepalive(self):
        self._send_command(self.SENSOR_SERVICE_ID, [0x00], False)


    def _set_handle_service(self):
        """ Create dictionary to to lookup service_id given the ble device handle """
        for service in self._client.services:
            for characteristic in service.characteristics:
                if characteristic.uuid[7].isnumeric():
                    self._handle_service[characteristic.handle] = int(characteristic.uuid[7])


    def is_connected(self):
        """
        Returns True if connected, False otherwise.
        """
        if self._client != None:
            return self._client.is_connected


    def disconnect(self):
        """
        Disconnect from the device
        """
        if self._client != None:
            self._loop.run_until_complete(self._async_disconnect())
        self._client = None


    async def _async_disconnect(self):
        uuid = self._set_uuid(self.SENSOR_SERVICE_ID, self.RECV_CMD_CHAR_ID)

        await self._client.stop_notify(uuid)
        await self._client.disconnect()       


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


    def _decode64(self, charVal):
        """
        Decode Base-64 character to corresponding integer
        0-9 	-> '0' - '9'
        10-25	-> 'K' - 'Z' -- Note: this funkiness is required due to an error in this code that was caught
        26-35	-> 'A' - 'J' -- after the wireless sensors went into production, so part of the bug stays
        36-61	-> 'a' - 'z' -- since the bug also exists in the matching sensor firmware code
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
            byteLength (int): Number of bytes the integer is suppoed to be

        Returns:
            Two' complement of an integer value
        """
        bit_len = byte_len * 8
        if value > (1<<(bit_len-1)):
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

        return sign * mantissa * 2**(exp-150)


    def _calc_4_params(self, raw, x1, y1, x2, y2):
        b = (x1*y2 - x2*y1)/(x1-x2)
        if (x1 != 0):
            m = (y1 - b)/x1
        if (x2 != 0):
            m = (y2 - b)/x2
        
        return m * raw + b


    def _calc_linear_params(self, raw, m, b):
        """
        Return corresponding value of an input using a basic linear equation

        Args:
            raw (float): Linear equation "x" value
            m (float): Slope
            b (float): y-intercept
        """
        return m * raw + b


    def _send_command(self, service_id, command, wait_for_response=False):
        """
        Sends a command to our device

        Args:
            service id (int): Sensor channel we are sending data to
            characteristic id (int): Characteristic we are sending data to
            command (bytearray): Bytes array of data we are sending
        
        Return:
            True or false for success or fail
        
        Raises:
            Error if we were unable to send command
        """
        uuid = self._set_uuid(service_id, self.SEND_CMD_CHAR_ID)
        
        data_to_write = bytes(command).hex()

        bleWrite = "BLE WRITE: >>>"
        bleWrite += data_to_write
        #print(bleWrite)

        try:
            self._loop.run_until_complete(self._async_write(uuid, command, wait_for_response))
        except:
            print('ERROR: BLE write failed')
            return False

        return True


    def _send_ack(self, service_id, command):
        """
        Write acknowledgement packet to sensor for continuous data

        Args:
            service id (int): Sensor channel we are sending data to
            command (bytearray): Bytes array that contains the packet number we last received
        """
        uuid = self._set_uuid(service_id, self.SEND_ACK_CHAR_ID)

        data_to_write = bytes(command).hex()

        bleWrite = "BLE WRITE: >>>"
        bleWrite += data_to_write
        #print(bleWrite)

        try:
            self._loop.run_until_complete(self._async_write(uuid, command, wait_for_response=False))
        except:
            print('ERROR: BLE write failed')
            return False

        return True


    async def _async_write(self, uuid, data_to_write, wait_for_response):
        await self._client.write_gatt_char(uuid, bytes(data_to_write), wait_for_response)


    async def _initialize_sensor_values(self):
        try:
            interface = self._xml_root.find("./Interfaces/Interface[@ID='%s']" % self._interface_id)

            device_sensors = [
                {
                    'id': int(c.get('ID')),
                    'name': c.get('NameTag'),
                    'sensor_id': int(c.get('SensorID')) if 'SensorID' in c.attrib else '',
                    'type': c.get('Type'),
                    'output_type': c.get('OutputType') if 'OutputType' in c.attrib else '',
                    'measurements': [],
                    'total_data_size': 0,
                    'factory_cal_ids': []
                }
                for c in interface.findall("./Channel")
            ]
            
            for sensor in device_sensors:
                sensor_data = self._xml_root.find("./Sensors/Sensor[@ID='%s']" % str(sensor['sensor_id']))
                if sensor_data:
                    sensor['name'] = sensor_data.get('Tag')
                    sensor['measurements'] = [m.get('NameTag') for m in sensor_data.findall("./Measurement[@Visible='1']")]
                    sensor['factory_cal_ids'] = [m.get('ID') for m in sensor_data.findall("./Measurement[@Type='FactoryCal']")]

            for sensor in device_sensors:
                if sensor['type'] == 'Pasport':
                    self._data_ack_counter[sensor['id']] = 0
                    self._data_stack[sensor['id']] = []
                    self._sensor_measurements[sensor['id']] = {}
                                        
                    xml_measurements = self._xml_root.find("./Sensors/Sensor[@ID='%s']" % sensor['sensor_id'])
                    for measurement in xml_measurements.findall("./Measurement"):
                        measurement_id = {int(measurement.get('ID')): measurement.attrib}
                        self._sensor_measurements[sensor['id']].update(measurement_id)

                    for sensor_m_id, sensor_m in self._sensor_measurements[sensor['id']].items():
                        sensor_m['ID'] = int(sensor_m['ID'])
                        sensor_m['Type'] = sensor_m['Type'] if 'Type' in sensor_m else ''
                        sensor_m['Visible'] = int(sensor_m['Visible']) if 'Visible' in sensor_m else 0
                        sensor_m['Internal'] = int(sensor_m['Internal']) if 'Internal' in sensor_m else 0
                        if 'DataSize' in sensor_m:
                            sensor_m['DataSize'] = int(sensor_m['DataSize'])
                            sensor['total_data_size'] += sensor_m['DataSize']
                        if 'Inputs' in sensor_m and sensor_m['Inputs'].isnumeric(): sensor_m['Inputs'] = int(sensor_m['Inputs'])
                        if 'Precision' in sensor_m and sensor_m['Precision'].isnumeric(): sensor_m['Precision'] = int(sensor_m['Precision'])
                        # if sensor_m['Type'] == 'FactoryCal':
                            # await self.read_factory_cal(sensor['id'])
                            # Do Factory Cal reading here
                        #TODO: This is a temporary workaround for the code node cart
                        if sensor_m['NameTag'] == "RawCartPosition":
                            sensor_m['DataSize'] = 0

                    # TODO: Factory Calibration
                    #await self.read_factory_cal(sensor['id'])

                    #print('got the cal')

                    # Initialize internal sensor measurement values
                    self._sensor_data[sensor['id']] = { m_id: None for m_id in self._sensor_measurements[sensor['id']] }
            
            # Initialize device measurement values
            self._measurement_sensor_ids = { measurement: sensor['id'] for sensor in device_sensors for measurement in sensor['measurements'] }
            self._data_results = { m: None for sensor in device_sensors for m in sensor['measurements'] }

            self._device_sensors = {sensor['name'] : sensor for sensor in device_sensors}

        except:
            print("Could not setup sensor measurements")


    def get_sensor_list(self):
        """
        Return list of sensor names that a device has
        """
        if self.is_connected() is None:
            raise self.DeviceNotConnected()

        return [sensor_name for sensor_name, sensor in self._device_sensors.items()]


    def get_measurement_list(self, sensor_name=None):
        """
        Return list of measurements that a device can read

        Args:
            sensor_name (string): Optional paramater to only return measurements for a sensor
        """
    
        if sensor_name == None:
            measurement_list = [measurement for measurement in self._data_results]
        else:
            measurement_list = self._device_sensors[sensor_name]['measurements'] if sensor_name in self._device_sensors else None

        return measurement_list


    def read_data(self, measurement):
        """
        Read a sensor measurement

        Args:
            measurement (string): name of measurement we want to read
        """

        if measurement == None:
            pass
        else:
            try:
                sensor_id = self._measurement_sensor_ids[measurement]
            except:
                raise self.MeasurementNotFound
            
            self._get_sensor_measurements(sensor_id)

            return self._data_results[measurement]

        return None


    def read_data_list(self, measurements):
        """
        Read multiple sensor measurements

        Args:
            measurement (List(string)): List of measurements that we want to read
        """

        if measurements == None:
            pass
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

        return None


    def get_measurement_unit(self, measurement):
        """
        Return a measurement's default units

        Args:
            measurement (string): name of measurement we want the units for
        """

        if measurement == None:
            pass

        else:
            try:
                sensor_id = self._measurement_sensor_ids[measurement]
                for m_id, m in self._sensor_measurements[sensor_id].items():
                    if m['NameTag'] == measurement:
                        return m['UnitType']
            except:
                raise self.InvalidParameter

        return None

            
    def get_measurement_unit_list(self, measurements):
        """
        Return default units for multiple measurements

        Args:
            measurements (List(string)): List of measurements that we want the units for
        """

        if measurements == None:
            pass
    
        else:
            try:
                sensor_ids = {self._measurement_sensor_ids[m] for m in measurements}

                measurement_units = {
                    measurement: m['UnitType']
                    for sensor_id in sensor_ids
                    for m_id, m in self._sensor_measurements[sensor_id].items()
                    for measurement in measurements
                    if m['NameTag'] == measurement
                }
                return measurement_units
            except:
                raise self.InvalidParameter

        return None
        

    async def _single_listen(self, service_id):
        uuid = self._set_uuid(service_id, self.RECV_CMD_CHAR_ID)
        await self._client.start_notify(uuid, self._notify_callback)
        await self._client.stop_notify(uuid)


    async def _notify_callback(self, handle, value):
        bleNotif = "BLE NOTIFY: <<<"
        bleNotif += " ".join( [ "%02X " % c for c in value ] ).strip()
        #print(bleNotif)

        # Reading measurement response
        if self._handle_service[handle] > 0:
            channel_id = self._handle_service[handle] - 1

            # Received periodic data
            if (value[0] <= 0x1F):
                
                # Add data to stack
                self._data_stack[channel_id] += value[1:]

                self._data_ack_counter[channel_id] += 1

                self._loop.create_task(self._decode_data(channel_id))
                #self.send_data()

                # Send acknowledgement package
                if (self._data_ack_counter[channel_id] > 8):
                    try:
                        self._data_ack_counter[channel_id] = 0
                        service_id = channel_id + 1
                        command = [ value[0] ]
                        self._send_ack(service_id, command)
                    except:
                        print('Problem sending acknowledgement command')
                return

            # Received single data packet
            elif (value[0] is self.GRSP_RESULT):
                # Valid data 
                if value[1] == 0x00:
                    if value[2] is self.GCMD_READ_ONE_SAMPLE: # Get single measurement packet
                        self._single_measurement_packet = value[3:]
                    elif value[2] == 1: #SPI Data (ex: AirLink Interface connected)
                        pasport_service_id = 1
                        self._send_command(pasport_service_id, [ 0x08 ], True)
                        self.loop.run_until_complete(self._single_listen(pasport_service_id))
                        #TODO: AirLink things

                # Error receiving data
                elif value[1] == 0x01:
                    print(f'Error on channel # {channel_id}')

            elif (value[0] == self.GEVT_SENSOR_ID):
                self._airlink_sensor_id = value[1]

        # Reading device response
        elif self._handle_service[handle] == 0:
            # Received single data packet
            if (value[0] is self.GRSP_RESULT):
                # Valid data 
                if value[1] == 0x00:
                    if value[2] is self.GCMD_READ_ONE_SAMPLE: # Get single measurement packet
                        self._single_measurement_packet = value[3:]

            # Get factory calibration
            elif (value[0] == 0x0A):
                self._factory_cal_params[value[1]] = []
                num_params = 4
                byte_len = 4
                data = value[2:]
                for p in range(num_params):
                    byte_value = 0
                    for d in range(byte_len):
                        stack_value = data.pop(0)
                        byte_value += stack_value * (2**(8*d))

                    self._factory_cal_params[value[1]].append(float(self._binary_float(byte_value, byte_len)))
            
                print('---factoryparams---')
                print(self._factory_cal_params)

            elif (value[0] == 0x0B):
                pass
            #print(handle)


    def _get_sensor_measurements(self, sensor_id):
        service_id = sensor_id + 1

        for sensor_name, sensor in self._device_sensors.items():
            if sensor['id'] == sensor_id:
                packet_size = sensor['total_data_size']

        one_shot_cmd = [ self.GCMD_READ_ONE_SAMPLE, packet_size ]

        self._send_command(service_id, one_shot_cmd, False)
        self.loop.run_until_complete(self._single_listen(service_id))

        self._data_stack[sensor_id] = self._single_measurement_packet
        self.loop.run_until_complete(self._decode_data(sensor_id))


    async def _decode_data(self, sensor_id):
        try:
            # Save and reset current data dictionary
            self._sensor_data_prev[sensor_id] = self._sensor_data[sensor_id].copy()
            self._sensor_data[sensor_id] = { m_id: None for m_id in self._sensor_measurements[sensor_id] }

            for m_id, raw_m in self._sensor_measurements[sensor_id].items():
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

            """
            print("===RAW===")
            print(self._sensor_data)
            print("=========")
            """

            for m_id, m in self._sensor_measurements[sensor_id].items():
                if self._sensor_data[sensor_id][m_id] == None:
                    result_value = self._get_measurement_value(sensor_id, m_id)
                    if 'Precision' in m and result_value != None:
                        result_value = round(result_value, m['Precision'])

                    val = {m_id: result_value}
                    self._sensor_data[sensor_id].update(val)

            # Set visible data variables
            try:
                for channel_id, measurements in self._sensor_measurements.items():
                    for m_id, m in measurements.items():
                        if (m['Visible'] == 1 and self._sensor_data[channel_id][m_id] != None):
                            result_val = { m['NameTag']: self._sensor_data[channel_id][m_id] }
                            self._data_results.update(result_val)
            except:
                print("Could not gather visible data values")

        except:
            print(m)
            print('Error: Could not decode the data')


    def _get_measurement_value(self, channel_id, measurement_id):
        m = self._sensor_measurements[channel_id][measurement_id]
        result_value = None
        input_value = None

        #print(self._sensor_data[channel_id])

        if m['Type'] == 'RawDigital' and self._sensor_data[channel_id][measurement_id] == None:
            #print('the raw is not there')
            pass

        if 'Inputs' in m:
            # Multiple Input
            ##print(m)
            if m['Type'] == 'ThreeInputVector':
                inputs = m['Inputs'].split(',')
                missing_param = False
                for val in inputs:
                    if self._sensor_data[channel_id][int(val)] is None:
                        missing_param = True
                        break
                if missing_param is False:
                    ax = self._sensor_data[channel_id][int(inputs[0])]
                    ay = self._sensor_data[channel_id][int(inputs[1])]
                    az = self._sensor_data[channel_id][int(inputs[2])]
                    result_value = math.sqrt(ax**2 + ay**2 + az**2)
            elif m['Type'] == 'Select': # For Current, Voltage and Accel
                inputs = m['Inputs'].split(',')

                need_input = int(inputs[0])

                if self._sensor_data[channel_id][need_input] is not None:
                    result_value = self._sensor_data[channel_id][need_input]
                else:
                    result_value = self._get_measurement_value(channel_id, need_input)

            # Single Input
            else:
                need_input = int(m['Inputs'])
                if self._sensor_data[channel_id][need_input] is not None:
                    input_value = self._sensor_data[channel_id][need_input]
                else:
                    input_value = self._get_measurement_value(channel_id, need_input)

        if (input_value is not None):
            if m['Type'] == 'UserCal':
                params = m['Params'].split(',')
                result_value = self._calc_4_params(input_value, float(params[0]), float(params[1]), float(params[2]), float(params[3]))

            elif m['Type'] == 'FactoryCal':
                if 'FactoryCalParams' in m and len(m['FactoryCalParams']) == 4:
                    params = m['FactoryCalParams']
                else:
                    params = m['Params'].split(',')
                result_value = self._calc_4_params(input_value, float(params[0]), float(params[1]), float(params[2]), float(params[3]))

            elif m['Type'] == 'LinearConv':
                params = m['Params'].split(',')
                result_value = self._calc_linear_params(input_value, float(params[0]), float(params[1]))

            elif m['Type'] == 'Derivative':
                #Ignore for now - This is why we have the _sensor_data_prev object
                #return None
                if self._sensor_data_prev[channel_id][m['Inputs']] != None:
                    prev_input_value = self._sensor_data_prev[channel_id][m['Inputs']]
                    result_value = (input_value - prev_input_value) / 2
            
            elif m['Type'] == 'RotaryPos':
                self._dropcount += input_value
                result_value = self._dropcount

        if ('Equation' in m):
            raw_equation = m['Equation']

            eqn_variables = re.findall(r"\[([0-9_]+)\]", raw_equation)

            for eVar in eqn_variables:
                bracket_val = '[' + eVar + ']'
                eVarKey = int(eVar)

                raw_equation = raw_equation.replace('^', '**')

                if self._sensor_data[channel_id][eVarKey] != None:
                    replace_with = str(self._sensor_data[channel_id][eVarKey])
                    raw_equation = raw_equation.replace(bracket_val, replace_with)
                else:
                    replace_with = str(self._get_measurement_value(channel_id, eVarKey))
                    raw_equation = raw_equation.replace(bracket_val, replace_with)

            if raw_equation.startswith('usound'):
                usound_eqn = raw_equation.replace('usound(','')
                usound_eqn = usound_eqn.replace(')','')
                usound_vals = usound_eqn.split(',')

                ping_echo_time = float(usound_vals[0])
                speed_of_sound = float(usound_vals[1])

                result_value = (ping_echo_time/1000000) * speed_of_sound / 2 # result in meters

            elif raw_equation.startswith('dewpoint'):
                dewpoint_eqn = raw_equation.replace('dewpoint(','')
                dewpoint_eqn = dewpoint_eqn.replace(')','')
                dewpoint_vals = dewpoint_eqn.split(',')

                temp_c = float(dewpoint_vals[0])
                relative_humidity = float(dewpoint_vals[1])
                vapor_pressure_sat = 6.11 * pow( 10, (7.5 * temp_c) / (237.7 + temp_c) )
                vapor_pressure_actual = (relative_humidity * vapor_pressure_sat) / 100

                result_value = (-443.22 + 237.7 * math.log(vapor_pressure_actual)) / (-math.log(vapor_pressure_actual) + 19.08)

            elif raw_equation.startswith('windchill'):
                windchill_eqn = raw_equation.replace('windchill(','')
                windchill_eqn = windchill_eqn.replace(')','')
                windchill_vals = windchill_eqn.split(',')

                temp_f = (9 * float(windchill_vals[0]) / 5) + 32
                wind_mph = float(windchill_vals[1]) * 2.237

                if( wind_mph < 3.0 or temp_f > 50.0 ):
                    wind_chill_f = temp_f
                else:
                    wind_chill_f = 35.74 + 0.6215 * temp_f - 35.75 * pow( wind_mph, 0.16 ) + 0.4275 * temp_f * pow( wind_mph, 0.16 )

                result_value = 5 * (wind_chill_f - 32) / 9
            
            elif raw_equation.startswith('heatindex'):
                heatindex_eqn = raw_equation.replace('heatindex(','')
                heatindex_eqn = heatindex_eqn.replace(')','')
                heatindex_vals = heatindex_eqn.split(',')

                temp_c = float(heatindex_vals[0])
                relative_humidity = float(heatindex_vals[1])
                vapor_pressure_sat = 6.11 * pow( 10, (7.5 * temp_c) / (237.7 + temp_c) )
                vapor_pressure_actual = (relative_humidity * vapor_pressure_sat) / 100

                result_value = temp_c + 0.55555 * (vapor_pressure_actual - 10.0)

            elif raw_equation.startswith('codenodepos'):
                None

            else:
                try:
                    raw_equation = raw_equation.replace('sqrt', 'math.sqrt')
                    raw_equation = raw_equation.replace('atan2', 'math.atan2')

                    result_value = eval(raw_equation)

                except:
                    # equation likely has a string in it
                    # print(f"Unable to calculate equation: {raw_equation}")
                    raise self.InvalidEquation()

        #print(f'Results: {result_value}')
        return result_value


    async def read_factory_cal(self, channel_id):
        """
        Read factory calibrations from sensor's built in memory
        """
        print('getting factory cal')
        factory_cal_count = 0

        for m_id, m in self._sensor_measurements[channel_id].items():
            if m['Type'] == 'FactoryCal':
                factory_cal_count += 1
                #print(m)

        if factory_cal_count > 0:
            # Transfer Block RAM Command
            ll_read = 128
            ll_storage = 3
            ll = ll_read + ll_storage

            address = channel_id + 2
            num_bytes = 16 * factory_cal_count
            service_id = self.SENSOR_SERVICE_ID
            
            command = [ self.GCMD_XFER_BURST_RAM, ll,
                        address & 0xFF, address>>8 & 0XFF, address>>16 & 0XFF, address>>24 & 0XFF,
                        num_bytes & 0xFF, num_bytes>>8 & 0XFF ]

            self._send_command(service_id, command, True)
            #await self._single_listen(service_id)

            #Start Block Command
            command = [ 0X09, 0X01, num_bytes & 0XFF, num_bytes>>8 & 0XFF, 16 ]

            self._send_command(service_id, command, True)
            #await self._single_listen(service_id)

            # Save Factory Calibration Parameters
            for m_id, m in self._sensor_measurements[channel_id].items():
                i = 0
                if m['Type'] == 'FactoryCal':
                    m['FactoryCalParams'] = self._factory_cal_params[i]

            self._factory_cal_params = {}


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

    class InvalidEquation(Exception):
        """Could not calculate the measurement"""
        pass


def main():

    pasco_device = PASCOBLEDevice()
    found_devices = pasco_device.scan()

    if found_devices:
        for i, ble_device in enumerate(found_devices):
            print(f'{i}: {ble_device.name}')
        
        selected_device = input('Select a device: ') if len(found_devices) > 1 else 0
        pasco_device.connect(found_devices[int(selected_device)])
    else:
        print("No Devices Found")
        exit(1)

    print(pasco_device.get_sensor_list())
    print(pasco_device.get_measurement_list())

    print(pasco_device.read_data('Temperature'))

    while False:
        value = pasco_device.read_data('Temperature')
        print(f'Temp: {value}')
        #value = pasco_device.read_data_list(['Position','Velocity','Acceleration'])
        #print(f"Pos: {value['Position']} Vel: {value['Velocity']} Accel: {value['Acceleration']}")
        time.sleep(1)
        #rez = pasco_device.read_data_list(['Accelerationx','Accelerationy','Accelerationz'])
        #print(f"X: {rez['Accelerationx']}, Y: {rez['Accelerationy']}, Z: {rez['Accelerationz']}")


if __name__ == "__main__":
    main()
