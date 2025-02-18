# sensors.py - Example code to connect to any pasco device and get a benchmark sample rate
from pasco import PASCOBLEDevice
import time

sensor = PASCOBLEDevice()
sensorID = '123-456'  # Put your 6-digit sensor ID here

print(f"Attempting to connect to sensor: {sensorID}")

attemptCount = 0
start_time = time.monotonic()
while attemptCount < 5:
    try:
        attemptCount += 1
        sensor.connect_by_id(sensorID)
        print("Connected to sensor")
        break
    except Exception as e:
        print(f"Retrying at {round(time.monotonic()-start_time, 2)} seconds...")
else:
    print(f"Could not connect to sensor: {sensorID}")
    exit()

for measurement in sensor.get_measurement_list():
    print(measurement)

start = time.monotonic()
for i in range(100):
    print(f"{i}: {sensor.read_data(sensor.get_measurement_list()[0])}")

end = time.monotonic()
print(f"{round(end-start, 3)} seconds elapsed")
print(f"{round(100/(end-start), 3)} Hz sample rate")

sensor.disconnect()