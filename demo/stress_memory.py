# stress_memory.py
import time

data = []
while True:
    data.append(bytearray(500 * 1024 * 1024))  # 200 MB per iteration
    time.sleep(1)
