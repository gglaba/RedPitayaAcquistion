import numpy as np
import matplotlib.pyplot as plt

# === Configuration ===
BIN_FILE = r'Data/CH1V_CH2V_2025_04_08_19_37_23.bin'  # Path to your binary file
CHANNEL = 'CH2'  # 'CH1' or 'CH2'

# === Load Binary Data ===
data = np.fromfile(BIN_FILE, dtype=np.float32)

# Split interleaved data into CH1 and CH2
ch1 = data[::2]
ch2 = data[1::2]

# Select the channel to plot
if CHANNEL == 'CH1':
    y = ch1
elif CHANNEL == 'CH2':
    y = ch2
else:
    raise ValueError("CHANNEL must be 'CH1' or 'CH2'")

# === Plot Data ===
plt.figure(figsize=(10, 6))
plt.plot(ch1, label=CHANNEL, color='red', linestyle='-', linewidth=0.8)
plt.plot(ch2, label=CHANNEL, color='blue', linestyle='-', linewidth=0.8)



plt.title(f'{CHANNEL} Signal from Binary File')
plt.xlabel('Sample Index')
plt.ylabel('Voltage (V)')
plt.grid(True)
plt.legend()
plt.tight_layout()

# Show the plot
plt.show()
