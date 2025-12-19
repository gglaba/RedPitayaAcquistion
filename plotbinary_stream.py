import numpy as np

filename = "Data/data_file_192.168.137.197_2025-12-18_09-37-31.bin"
data = np.fromfile(filename, dtype=np.int16)

block_size = 16384  # Replace with your actual block size
num_blocks = len(data) // (2 * block_size)

ch1 = []
ch2 = []

for i in range(num_blocks):
    start = i * 2 * block_size
    ch1.extend(data[start : start + block_size])
    ch2.extend(data[start + block_size : start + 2 * block_size])

ch1 = np.array(ch1)
ch2 = np.array(ch2)
import matplotlib.pyplot as plt

plt.figure(figsize=(10,4))
plt.subplot(2,1,1)
plt.title("CH1")
plt.plot(ch1)
plt.subplot(2,1,2)
plt.title("CH2")
plt.plot(ch2)
plt.tight_layout()
plt.show()