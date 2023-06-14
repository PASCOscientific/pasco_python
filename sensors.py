# sensors.py
# connect to any pasco device and get a benchmark sample rate

from src.pasco import PASCOBLEDevice
import time

sensor = PASCOBLEDevice()
sensor.connect_by_id('651-400')
[print(measurement) for measurement in sensor.get_measurement_list()]

start = time.monotonic()
for i in range(100):
    print(f"{i}: {sensor.read_data(f'{sensor.get_measurement_list()[0]}')}")

end = time.monotonic()
print(f"{end-start} seconds elapsed")
print(f"{100/(end-start)} Hz sample rate")


sensor.disconnect()