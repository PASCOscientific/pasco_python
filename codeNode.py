from src.pasco import PASCOBLEDevice, CodeNodeDevice, Icons
import time

code_node = CodeNodeDevice()
code_node.connect_by_id('614-906')

start = time.monotonic()
for i in range(100):
    print(f"{i}: {code_node.read_data('Brightness')}")

end = time.monotonic()
print(f"{end-start} seconds elapsed")
print(f"{100/(end-start)} Hz sample rate")

code_node.reset()

code_node.disconnect()