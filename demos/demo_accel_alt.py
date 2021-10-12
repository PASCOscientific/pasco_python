from pasco.pasco_ble_device import PASCOBLEDevice
import time

def test():
    Bob = PASCOBLEDevice()
    Bob.connect_by_id('412-335')

    time.sleep(1)

    print(Bob.get_measurement_list())

    time.sleep(1)

    # print(Bob.read_data('Force'))
    print('Ax: ' + str(Bob.read_data('Accelerationx')))
    print('Ay: ' + str(Bob.read_data('Accelerationy')))
    print('Az: ' + str(Bob.read_data('Accelerationz')))
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
    time.sleep(1)

    Bob.disconnect()

if __name__ == "__main__":
    test()
