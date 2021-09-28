from '../src/pasco/pasco_ble_device' import PASCOBLEDevice
# from pasco.code_node_device import CodeNodeDevice
# from pasco.character_library import Icons
from time import sleep


Bob = PASCOBLEDevice()
Bob.connect_by_id('412-335')

sleep(1)

print(Bob.get_measurement_list())

sleep(1)

# print(Bob.read_data('Force'))
print(Bob.read_data('Accelerationx'))
print(Bob.read_data('Accelerationy'))
print(Bob.read_data('Accelerationz'))
print(Bob.read_data('AccelerationResultant'))
# print(Bob.read_data('Position'))
# print(Bob.read_data('Velocity'))
# print(Bob.read_data('Acceleration'))
print(Bob.read_data('AngularVelocityx'))
print(Bob.read_data('AngularVelocityy'))
print(Bob.read_data('AngularVelocityz'))
print(Bob.read_data('Altitude'))
# print(Bob.read_data('Speed'))
# print(Bob.read_data('UVIndex'))
# print(Bob.read_data('Illuminance'))
# print(Bob.read_data('SolarIrradiance'))
# print(Bob.read_data('SolarPAR'))
# print(Bob.read_data('WindDirection'))
# print(Bob.read_data('MagneticHeading'))
# print(Bob.read_data('TrueHeading'))
sleep(1)

Bob.disconnect()