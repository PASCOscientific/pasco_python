# codeNode.py - Example code for interfacing with a CodeNode device
from pasco import CodeNodeDevice
import time

code_node = CodeNodeDevice()
try:
    code_node.connect_by_id('123-456')  # Put your 6-digit sensor ID here
except Exception as e:
    print(f"Could not connect to sensor: {e}")
    exit()

start = time.monotonic()
for i in range(100):
    print(f"{i}: {code_node.read_data('Brightness')}")

end = time.monotonic()
print(f"{end-start} seconds elapsed")
print(f"{100/(end-start)} Hz sample rate")

code_node.reset()
code_node.disconnect()