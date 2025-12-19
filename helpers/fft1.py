import numpy as np
import matplotlib.pyplot as plt

# === Configuration ===
BIN_FILE = r'Data/data_file_192.168.137.197_2025-12-18_19-49-20.bin'  # Path to your binary file
CHANNEL = 'CH2'  # 'CH1' or 'CH2'
SAMPLING_RATE = 122000  # Sampling rate in Hz (adjust based on your setup)

# === Load Binary Data ===
data = np.fromfile(BIN_FILE, dtype=np.int16)

# Split interleaved data into CH1 and CH2
ch1 = data[::2]
ch2 = data[1::2]

# Select the channel to process
if CHANNEL == 'CH1':
    selected_data = ch1
elif CHANNEL == 'CH2':
    selected_data = ch2
else:
    raise ValueError("Invalid CHANNEL. Choose 'CH1' or 'CH2'.")

# === Perform FFT ===
n = len(selected_data)  # Number of samples
frequencies = np.fft.fftfreq(n, d=1/SAMPLING_RATE)  # Frequency bins
fft_values = np.fft.fft(selected_data)  # Compute FFT
magnitude = np.abs(fft_values)  # Magnitude of FFT

# Only keep the positive half of the spectrum
positive_freqs = frequencies[:n // 2]
positive_magnitude = magnitude[:n // 2]

# === Plot FFT ===
plt.figure(figsize=(10, 6))
plt.plot(positive_freqs, positive_magnitude, color='blue', linewidth=0.8)
plt.title(f'FFT of {CHANNEL}')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Magnitude')
plt.grid(True)
plt.tight_layout()

# Show the plot
plt.show()