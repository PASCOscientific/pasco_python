import asyncio
import character_library
import dweepy
import math
import os
import re
import requests
import time
import xml.etree.ElementTree as ET

from bleak import BleakClient, discover
from uuid import UUID


class PASCOBLEDevice():
    """
    PASCO Device object that has functions for connecting and getting data
    """
    SENSOR_SERVICE_ID = 0
    V_SENSOR_1_SERVICE_ID = 1

    SEND_CMD_CHAR_ID = 2
    RECV_CMD_CHAR_ID = 3
    RECV_PERIODIC_CHAR_ID = 4
    SEND_ACK_CHAR_ID = 5

    GCMD_SET_SAMPLE_PERIOD = 0X01
    GCMD_READ_ONE_SAMPLE = 0x05
    GCMD_START_SAMPLING = 0X06
    GCMD_STOP_SAMPLING = 0X07
    GCMD_XFER_BURST_RAM = 0X0E

    GCMD_CODENODE_CMD = 0x37
    CODENODE_CMD_SET_LED = 0X02
    CODENODE_CMD_SET_LEDS = 0X03
    CODENODE_CMD_SET_SOUND_FREQ = 0X04

    GRSP_RESULT = 0XC0                      # Generic response packet
    GEVT_SENSOR_ID = 0x82                   # Get Sensor ID (for AirLink)


    def __init__(self, sensor_name=None, select_measurement=None):
        """
        Create a PASCO BLE Device object

        Args:
            sensor_name (string): Optional - include a sensor name/6-digit ID to connect quickly
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

        self._channels = []
        self._handle_service = {}
        self._data_stack = {}
        self._single_measurement = []
        self._channel_measurements = {}
        self._factory_cal_params = {}
        self._sensor_data = {}
        self._sensor_data_prev = {}
        self._xml_root = None

        self._results = {}
        self._variable_channel = {}

        if sensor_name:
            self.scan(sensor_name, select_measurement)

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
    def results(self):
        return self._results

    @property
    def channels(self):
        return self._channels

    @property
    def variable_channel(self):
        return self._variable_channel


    def scan(self, sensor_name=None, select_measurement=None):
        """
        Scans for all PASCO devices

        Args:
            sensor_name (str): Sensor name to search for, can be the type or sensor's serial id

        Returns:
            List of devices that match PASCO device names
        """
        try:
            # Load Datasheet
            tree = ET.parse('datasheets.xml')
            self._xml_root = tree.getroot()

            if sensor_name is None:
                # Read PASCO BLE Device Types from Datasheet
                pasco_device_names = { 
                    item.get('AdvertisingName')
                    for item in self._xml_root.findall('./Interfaces/Interface')
                    if item.get('AdvertisingName')
                }
            else:
                # Look for sensor name that matches
                pasco_device_names = { sensor_name }

            # Get list of PASCO BLE Devices found
            found_devices = self._loop.run_until_complete(self._async_scan(pasco_device_names))

            if found_devices == None or len(found_devices) == 0:
                raise
            elif sensor_name and len(found_devices) == 1:
                if select_measurement is None:
                    select_measurement = 'a'

                self.connect(found_devices[0],select_measurement)                    
            else:
                return found_devices
        except:
            print('No PASCO Bluetooth devices found.')
            exit(1)


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
            sensor_service_id: The sensor service we're connecting to
            uuid_char_id: The characteristic we want to communicate with
        
        Returns:
            uuid object
        """
        uuid = "4a5c000" + str(service_id) + "-000" + str(characteristic_id) + "-0000-0000-5c1e741f1c00"
        return UUID(uuid)


    def connect(self, ble_device, select_measurement = None):
        """
        Connect to a bluetooth device

        Args:
            ble_device(BLEDevice): Device object discovered up when doing scan
            select_measurement (int/str): 'a' or 0+ Optional - to preselect sensor measurement that we want to activate
        """
        #self._connect(ble_device.address)
        self._client = BleakClient(ble_device.address)

        try:
            self._loop.run_until_complete(self._async_connect())
        except ConnectionError:
            print("Could not connect")
            exit(1)

        else:
            self._set_device_params(ble_device)
            print("\nConnected to " + self._name)

            if self._dev_type == 'AirLink':
                self._send_command(self.V_SENSOR_1_SERVICE_ID, [0x08], True)
                self.loop.run_until_complete(self.single_listen(self.V_SENSOR_1_SERVICE_ID))

            self._loop.run_until_complete(self._set_sensor_measurements(select_measurement))


    async def _async_connect(self):
        await self._client.connect()
        if not self._client.is_connected:
            return False

        self._set_handle_service()

        uuid = self._set_uuid(self.SENSOR_SERVICE_ID, self.RECV_CMD_CHAR_ID)
        await self._client.start_notify(uuid, self._notify_callback)


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


    def stop(self):
        """
        Stop data collection (sensor remains connected)

        Returns:
            boolean: True on success or False on failure
        """
        try:
            self._send_command(self.SENSOR_SERVICE_ID, [ self.GCMD_STOP_SAMPLING ])
            print('Data collection stopped')
            return True

        except:
            print('Error trying to stop the sensor')
            return False


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
            self._loop.create_task(self._async_write(uuid, command, wait_for_response))
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
            self._loop.create_task(self._async_write(uuid, command, wait_for_response=False))
        except:
            print('ERROR: BLE write failed')
            return False

        return True


    async def _async_write(self, uuid, data_to_write, wait_for_response):
        await self._client.write_gatt_char(uuid, data_to_write, wait_for_response)


    async def _set_sensor_measurements(self, select_measurement=None):
        """
        Get sensor measurements and channels from the datasheet
        """
        try:
            interface = self._xml_root.find("./Interfaces/Interface[@ID='%s']" % self._interface_id)

            sensor_channels = [
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
            
            if (self._airlink_sensor_id != None):
                sensor = self._xml_root.find("./Sensors/Sensor[@ID='%s']" % self._airlink_sensor_id)
                sensor_channels[0]['sensor_id'] = sensor.get('ID')
                sensor_channels[0]['name'] = sensor.get('Tag')

            for i, channel in enumerate(sensor_channels):
                sensor_measurements = self._xml_root.find("./Sensors/Sensor[@ID='%s']" % str(channel['sensor_id']))
                if sensor_measurements:
                    channel['measurements'] = [x.get('NameTag') for x in sensor_measurements.findall("./Measurement[@Visible='1']")]
                    channel['factory_cal_ids'] = [m.get('ID') for m in sensor_measurements.findall("./Measurement[@Type='FactoryCal']")]


            # Default to channel 0 if device only has 1 sensor
            if len(sensor_channels) == 1:
                channel = sensor_channels[0]
                self._channels = [ channel ]
                channel_list = ", ".join(channel['measurements'])
                print(f"{interface.get('NameTag')} ({channel_list})")

                #PUT AIRLINK INSTRUCTIONS HERE

            elif len(sensor_channels) > 1:
                #print("\nSelect a measurement group to activate. Separate multiple values with a comma, ex: 0,2")

                for i, channel in enumerate(sensor_channels):
                    sensor_measurements = self._xml_root.find("./Sensors/Sensor[@ID='%s']" % str(channel['sensor_id']))
                    if sensor_measurements:
                        channel_list = ", ".join(channel['measurements'])

                        print(f"{i}: {channel['name']} ({channel_list})")

                print(f'a: All')

                #TODO: For testing
                if select_measurement is not None:
                    user_selection = select_measurement
                else:
                    user_selection = input("Enter [default: a]: ")
                #user_selection = 'a'

                print("\n")

                if isinstance(user_selection, int) or user_selection.isnumeric():
                    self._channels.append(sensor_channels[int(user_selection)])
                elif len(user_selection) <= 1:
                    if user_selection == 'a' or user_selection == '':
                        self._channels = sensor_channels
                else:
                    self._channels = [sensor_channels[int(x)] for x in user_selection.split(",")]

            for channel in self._channels:
                if channel['type'] == 'Pasport':
                    channel_id = channel['id']

                    self._data_ack_counter[channel_id] = 0
                    self._data_stack[channel_id] = []
                    self._channel_measurements[channel_id] = {}
                    
                    xml_measurements = self._xml_root.find("./Sensors/Sensor[@ID='%s']" % channel['sensor_id'])
                    for m in xml_measurements.findall("./Measurement"):
                        m_value = {int(m.get('ID')): m.attrib}
                        self._channel_measurements[channel_id].update(m_value)

                    # Initialize measurement values
                    for m_id, m in self._channel_measurements[channel_id].items():
                        m['ID'] = int(m['ID'])
                        m['Type'] = m['Type'] if 'Type' in m else ''
                        m['Visible'] = int(m['Visible']) if 'Visible' in m else 0
                        m['Internal'] = int(m['Internal']) if 'Internal' in m else 0
                        if 'DataSize' in m:
                            m['DataSize'] = int(m['DataSize'])
                            channel['total_data_size'] += m['DataSize']
                        if 'Inputs' in m and m['Inputs'].isnumeric(): m['Inputs'] = int(m['Inputs'])
                        if 'Precision' in m and m['Precision'].isnumeric(): m['Precision'] = int(m['Precision'])
                        #if m['Type'] == 'Constant':
                        #    self._sensor_data[channel_id][m['ID']] = float(m['Value'])
                        #if m['Type'] == 'FactoryCal':
                            #Do Factory Cal reading here
                        #TODO: This is a temporary workaround for the code node cart
                        if m['NameTag'] == "RawCartPosition":
                            m['DataSize'] = 0

                    # Setup Default Measurement Data
                    self._sensor_data[channel_id] = { m_id: None for m_id in self._channel_measurements[channel_id] }
                    self._results = { m: None for c in self._channels for m in c['measurements'] }
                    self._variable_channel = { m: c['id'] for c in self._channels for m in c['measurements'] }
                    await self.read_factory_cal(channel_id)

        except:
            print("Could not set sensor measurements")


    async def start_listener(self, service_id):
        uuid = self._set_uuid(service_id, self.RECV_PERIODIC_CHAR_ID)
        await self._client.start_notify(uuid, self._notify_callback)

        while self._client.is_connected:
            await asyncio.sleep(1)


    async def single_listen(self, service_id):
        uuid = self._set_uuid(service_id, self.RECV_CMD_CHAR_ID)
        await self._client.start_notify(uuid, self._notify_callback)


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

                self._loop.create_task(self.decode_data(channel_id))
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
                if value[1] is 0x00:
                    if value[2] is self.GCMD_READ_ONE_SAMPLE: # Get single measurement packet
                        self._single_measurement = value[3:]
                    elif value[2] == 1: #SPI Data (ex: AirLink Interface connected)
                        pasport_service_id = 1
                        self._send_command(pasport_service_id, [ 0x08 ], True)
                        self.loop.run_until_complete(self.single_listen(pasport_service_id))
                        #TODO: AirLink things

                # Error receiving data
                elif value[1] is 0x01:
                    print(f'Error on channel # {channel_id}')

            elif (value[0] == self.GEVT_SENSOR_ID):
                self._airlink_sensor_id = value[1]

        # Reading device response
        elif self._handle_service[handle] == 0:
            # Received single data packet
            if (value[0] is self.GRSP_RESULT):
                # Valid data 
                if value[1] is 0x00:
                    if value[2] is self.GCMD_READ_ONE_SAMPLE: # Get single measurement packet
                        self._single_measurement = value[3:]

            # Get factory calibration
            elif (value[0] is 0x0A):
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
            
            elif (value[0] is 0x0B):
                pass
            #print(handle)


    def _get_sensor_measurement(self, channel_id):
        service_id = channel_id + 1

        for chan in self._channels:
            if chan['id'] == channel_id:
                packet_size = chan['total_data_size']

        one_shot_cmd = [ self.GCMD_READ_ONE_SAMPLE, packet_size ]

        self._send_command(service_id, one_shot_cmd, True)
        self.loop.run_until_complete(self.single_listen(service_id))

        self._data_stack[channel_id] = self._single_measurement
        self.loop.run_until_complete(self.decode_data(channel_id))


    async def decode_data(self, channel_id):
        try:
            # Save and reset current data dictionary
            self._sensor_data_prev = self._sensor_data.copy()
            self._sensor_data[channel_id] = { m_id: None for m_id in self._channel_measurements[channel_id] }
            for m_id, raw_m in self._channel_measurements[channel_id].items():
                result_value = None

                if raw_m['Type'] == 'RawDigital':
                    result_value = 0
                    for d in range(raw_m['DataSize']):
                        if len(self._data_stack[channel_id]):
                            stack_value = self._data_stack[channel_id].pop(0)
                            result_value += stack_value * (2**(8*d))

                    if (raw_m['DataSize'] == 4 or ('TwosComp' in raw_m and int(raw_m['TwosComp']) == 1)):
                        result_value = self._twos_comp(result_value, raw_m['DataSize'])

                elif raw_m['Type'] == 'Direct':
                    byte_value = 0
                    for d in range(raw_m['DataSize']):
                        if len(self._data_stack[channel_id]):
                            stack_value = self._data_stack[channel_id].pop(0)
                            byte_value += stack_value * (2**(8*d))

                    if raw_m['DataSize'] == 4:
                        byte_value = self._twos_comp(byte_value, raw_m['DataSize'])
                        result_value = float(self._binary_fraction(byte_value))
                    
                    result_value = round(result_value, raw_m['Precision']) if 'Precision' in raw_m else result_value

                elif raw_m['Type'] == 'Constant':
                    result_value = float(raw_m['Value'])
                    result_value = round(result_value, raw_m['Precision']) if 'Precision' in raw_m else result_value

                val = {raw_m['ID']: result_value}
                self._sensor_data[channel_id].update(val)

            """
            print("===RAW===")
            print(self._sensor_data)
            print("=========")
            """

            for m_id, m in self._channel_measurements[channel_id].items():
                if self._sensor_data[channel_id][m_id] == None:
                    result_value = self._get_measurement_value(channel_id, m_id)
                    if 'Precision' in m and result_value != None:
                        result_value = round(result_value, m['Precision'])

                    val = {m_id: result_value}
                    self._sensor_data[channel_id].update(val)

            #"""
            #print("***CALC***")
            #print(self._sensor_data)
            #print(str(self._sensor_data) + '\r', end='')
            #print("**********")
            #"""

            # Set visible data variables
            try:
                for channel_id, measurements in self._channel_measurements.items():
                    for m_id, m in measurements.items():
                        if (m['Visible'] == 1 and self._sensor_data[channel_id][m_id] != None):
                            result_val = { m['NameTag']: self._sensor_data[channel_id][m_id] }
                            self._results.update(result_val)
            except:
                print("Could not gather visible data values")

        except:
            print(m)
            print('Error: Could not get the measurement value')


    def _get_measurement_value(self, channel_id, measurement_id):
        m = self._channel_measurements[channel_id][measurement_id]
        result_value = None

        if 'Inputs' in m:
            # Multiple Input
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
            elif m['Type'] == 'Select':
                inputs = m['Inputs'].split(',')
                result_value = self._sensor_data[channel_id][int(inputs[1])]
            # Single Input
            else:
                if self._sensor_data[channel_id][m['Inputs']] is not None:
                    input_value = self._sensor_data[channel_id][m['Inputs']]
                else:
                    input_value = self._get_measurement_value(channel_id, m['Inputs'])

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
            return None
            """
            if self._sensor_data_prev[channel_id][m['Inputs']] != None:
                prev_input_value = self._sensor_data_prev[channel_id][m['Inputs']]
                result_value = (input_value - prev_input_value) / 2
            """

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
                uSoundVars = raw_equation.replace('usound(','')
                uSoundVars = uSoundVars.replace(')','')

                usoundVals = uSoundVars.split(',')

                pingEchoTime = float(usoundVals[0])
                speedOfSound = float(usoundVals[1])

                result_value = (pingEchoTime/1000000) * speedOfSound / 2 # result in meters


            elif raw_equation.startswith('codenodepos'):
                result_value = None
                
            else:
                try:
                    raw_equation = raw_equation.replace('sqrt', 'math.sqrt')
                    raw_equation = raw_equation.replace('atan2', 'math.atan2')

                    result_value = eval(raw_equation)

                except:
                    # equation likely has a string in it
                    print(f"Unable to calculate equation: {raw_equation}")

        return result_value


    def potential_values(self):
        """
        Show list of measurement variables
        """
        print('\nSensor Measurement Variables:')
        for m in self._results:
            print(m)

    def value_of(self, variable_name):
        try:
            channel_id = self._variable_channel[variable_name]
            self._get_sensor_measurement(channel_id)

            #print(self._results)

            return self._results[variable_name]
        except KeyError:
            print(f"Variable {variable_name} does not exist in the selected measurements")
            raise

    def start_periodic(self, seconds, ext_callback_fn):
        """
        Start periodic sampling (continuous) for selected channels

        Args:
            seconds: in microseconds or set to 0 to disable
        """

        sample_size = self._channels[0]['total_data_size'] if self._airlink_sensor_id is not None else 0

        try:
            useconds = int(seconds * 1000000) #Convert to microseconds
            sample_rate = [ self.GCMD_SET_SAMPLE_PERIOD,
                    useconds & 0xFF, useconds>>8 & 0XFF, useconds>>16 & 0XFF, useconds>>24 & 0XFF,
                    sample_size, 0X00 ]
            start_cmd = [ self.GCMD_START_SAMPLING ]

            for channel in self._channels:
                if channel['type'] == 'Pasport':
                    service_id = channel['id'] + 1
                    self._send_command(service_id, sample_rate)
                    self._send_command(service_id, start_cmd)

            synchronous_functions = [
                self.start_listener(channel['id']+1) for channel in self._channels if channel['type'] == 'Pasport'
            ]
            
            synchronous_functions.append(ext_callback_fn)

            self._loop.run_until_complete(asyncio.wait(synchronous_functions))

        except:
            print("Could not start periodic sampling")


    def _led_0_to_10(self, intensity):
        """
        Convert a 0-10 value to 0-255

        Args:
            intensity (int): [0-10] brightness of LED
        """
        if intensity <= 0:
            return 0
        elif intensity > 10:
            return 255

        # Got this equation by curve-fitting gamma correction values from the LED controller datasheet
        result = int(2.1 * intensity ** 2 + 4.93 * intensity - 1.23)

        if result <= 0:
            return 0
        if result > 255:
            return 255
        else:
            return result


    def code_node_set_led(self, x, y, intensity):
        """
        Set an individual LED on the 5x5 matrix

        Args:
            x (int): [0-4] column value (top to bottom)
            y (int): [0-4] row value (left to right)
            intensity (int): [0-10] brightness control of LED
        """
        ledIndex = 20 - (y * 5) + x # Converts xy position to LED index
        ledIntensity = self._led_0_to_10(intensity)

        cmd = [ self.GCMD_CODENODE_CMD, self.CODENODE_CMD_SET_LED, ledIndex, ledIntensity ]
        self._send_command(0, cmd, True)
        self.loop.run_until_complete(self.single_listen(self.SENSOR_SERVICE_ID))


    def code_node_set_leds(self, led_array=[], intensity=5):
        """
        Set multiple LEDs on the 5x5 Matrix

        Args:
            led_array (List): [[x0,y0]... [x4,y4]] A list of coordinate pairs, ex: [[4,4], [0,4], [2,2]]
                ---------------------------
                | 0,0  1,0  2,0  3,0  4,0 |
                | 0,1  1,1  2,1  3,1  4,1 |
                | 0,2  1,2  2,2  3,2  4,2 |
                | 0,3  1,3  2,3  3,3  4,3 |
                | 0,4  1,4  2,4  3,4  4,4 |
                ---------------------------
            intensity (int): [0-10] brightness control of LEDs in the array
        """
        led_activate = 0
        for x,y in led_array:
            led_index = 20 - (y * 5) + x # Converts xy position to LED index
            led_activate += 2 ** led_index

        led_intensity = self._led_0_to_10(intensity)

        cmd = [ self.GCMD_CODENODE_CMD, self.CODENODE_CMD_SET_LEDS,
                led_activate & 0xFF, led_activate>>8 & 0XFF, led_activate>>16 & 0XFF, led_activate>>24 & 0XFF,
                led_intensity ]
        self._send_command(0, cmd)
        self.loop.run_until_complete(self.single_listen(self.SENSOR_SERVICE_ID))


    def code_node_set_rgb_leds(self, r=0, g=0, b=0):
        """
        Set the //code.Node's RGB LED
        
        Args:
            r (int): [0-10] brightness control of Red LED
            g (int): [0-10] brightness control of Green LED
            b (int): [0-10] brightness control of Blue LED
        """

        led_r = self._led_0_to_10(r)
        led_g = self._led_0_to_10(g)
        led_b = self._led_0_to_10(b)

        cmd = [ self.GCMD_CODENODE_CMD, self.CODENODE_CMD_SET_LEDS, led_r, led_g, led_b, 0X80, 0X00 ]
        self._send_command(0, cmd, True)
        self.loop.run_until_complete(self.single_listen(self.SENSOR_SERVICE_ID))


    def code_node_set_sound_frequency(self, frequency):
        """
        Control the code node's built in speaker output frequency

        Args:
            Frequency (in hertz)
        """
        cmd = [ self.GCMD_CODENODE_CMD, self.CODENODE_CMD_SET_SOUND_FREQ, frequency & 0xFF, frequency>>8 & 0XFF ]
        self._send_command(0, cmd, True)
        self.loop.run_until_complete(self.single_listen(self.SENSOR_SERVICE_ID))


    def code_node_scroll_text(self, word):
        matrix = character_library.get_word(word)
        #print(matrix)
        for disp in matrix:
            self.code_node_set_leds(disp)


    def code_node_show_icon(self, icon):
        matrix = character_library.get_icon(icon)
        #print(matrix)
        self.code_node_set_leds(matrix)


    def code_node_reset(self):
        self.code_node_set_rgb_leds(0,0,0)
        self.code_node_set_leds([])
        self.code_node_set_sound_frequency(0)


    async def read_factory_cal(self, channel_id):
        """
        Read factory calibrations from sensor's built in memory
        """
        factory_cal_count = 0

        for m_id, m in self._channel_measurements[channel_id].items():
            if m['Type'] == 'FactoryCal':
                factory_cal_count += 1
            #print(m)

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
        await self.single_listen(service_id)

        #Start Block Command
        command = [ 0X09, 0X01, num_bytes & 0XFF, num_bytes>>8 & 0XFF, 16 ]

        self._send_command(service_id, command, True)
        await self.single_listen(service_id)

        # Save Factory Calibration Parameters
        for m_id, m in self._channel_measurements[channel_id].items():
            i = 0
            if m['Type'] == 'FactoryCal':
                m['FactoryCalParams'] = self._factory_cal_params[i]

        self._factory_cal_params = {}



#############################################################
# Main Function
#############################################################
async def period_callback_fn(device = PASCOBLEDevice, sample_period = 1):
    """
    This function allows you to manipulate the periodic data
    """
    
    session = requests.Session()
    timer = time.time()

    print('Starting callback function')
    while True:
        #Do all periodic tasks here

        print(device.results)
        
        await asyncio.sleep(sample_period)

        send_interval = 5
        if (time.time() - send_interval > timer):
            timer = time.time()
            try:
                dweepy.dweet_for(f'pasco-{device.serial_id}', device.results, session=session)
            except:
                print("Could not send data")
                pass

def main():
    # Scan for PASCO Devices
    device = PASCOBLEDevice()
    found_devices = device.scan()
    
    print('\nDevices Found')
    for i, ble_device in enumerate(found_devices):
        display_name = ble_device.name.split('>')
        print(f'{i}: {display_name[0]}')

    # Auto connect if only one sensor found
    selected_device = input('Select a device: ') if len(found_devices) > 1 else 0
    
    ble_device = found_devices[int(selected_device)]

    device.connect(ble_device,'a')

    device.potential_values()

    #device.read_factory_cal(1)

    #sample_period = 1
    #device.start_periodic(sample_period, period_callback_fn(device, sample_period))

    #device = PASCOBLEDevice('//code.Node','a')
    #device2 = PASCOBLEDevice('Force','a')
    #device = PASCOBLEDevice('Weather','a')
    #device = PASCOBLEDevice('163-867')
    #device2 = PASCOBLEDevice('090-903')

    #device._send_command(service_id, [0x0F, 0x0F], True)
    #device.loop.run_until_complete(device.single_listen(service_id))
    
    #device._send_command(1, [0x08], True)
    #device.loop.run_until_complete(device.single_listen(1))
    
    #while True:
    #device.code_node_scroll_text('HUMBERTO')


    #device.code_node_scroll_text('PASCO')

    #print(device.value_of('Force'))
    #print(device2.value_of('RawUncalCO2Concentration'))

    #sample_period = 3
    
    #led_array = [[1,0], [3,0], [2,2], [0,3], [1,4], [2,4], [3,4], [4,3]] # Smiley face

    #device.code_node_set_leds(led_array)
    #device.code_node_set_rgb_leds()


    #print(device.value_of('MagneticHeading'))

    # Send Dweet
    #dweepy.dweet_for(f'pasco-{device._dev_type}2', device.results)
    #device.start_periodic(1) #TODO: Send sample rate inside here
    
    #device.stop()


print(f"pid {os.getpid()}: press Ctrl+C to quit")

if __name__ == "__main__":
    main()
