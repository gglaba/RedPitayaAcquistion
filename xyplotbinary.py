import numpy as np
import matplotlib.pyplot as plt

# === Configuration ===
BIN_FILE = r'Merged\data_file_2025-12-15_14-49-48.bin'  # Path to your binary file
CHANNEL = 'CH1'  # 'CH1' or 'CH2'

# === Load Binary Data ===
data = np.fromfile(BIN_FILE, dtype=np.float32)

# Split interleaved data into CH1 and CH2
ch1 = data[::2]
ch2 = data[1::2]

# Select the channel to plot


# === Plot Data ===
plt.figure(figsize=(10, 6))
plt.plot(ch1, label=CHANNEL, color='red', linestyle='--', linewidth=0.8)
plt.plot(ch2, label=CHANNEL, color='blue', linestyle='-', linewidth=0.8)



plt.title(f'{CHANNEL}')
plt.xlabel('Index')
plt.ylabel('Voltage')
plt.grid(True)
plt.legend()
plt.tight_layout()

# Show the plot
if __name__ == "__main__":
	plt.show()
