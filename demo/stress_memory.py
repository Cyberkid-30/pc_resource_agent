# stress_memory.py
import time

data = []
while True:
    data.append(bytearray(50 * 1024 * 1024))  # 50 MB per iteration
    time.sleep(1)
