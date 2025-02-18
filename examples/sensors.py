# sensors.py - Example code to connect to any pasco device and get a benchmark sample rate
from pasco import PASCOBLEDevice
import time

sensor = PASCOBLEDevice()
try:
    sensorID = '123-456' # Put your 6-digit sensor ID here
    sensor.connect_by_id(sensorID)
except Exception as e:
    print(f"Could not connect to sensor: {sensorID}")
    print(type(e))
    exit()

for measurement in sensor.get_measurement_list():
    print(measurement)

start = time.monotonic()
for i in range(100):
    print(f"{i}: {sensor.read_data(sensor.get_measurement_list()[0])}")

end = time.monotonic()
print(f"{end-start} seconds elapsed")
print(f"{100/(end-start)} Hz sample rate")

sensor.disconnect()