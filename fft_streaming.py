import numpy as np
import matplotlib.pyplot as plt
from nptdms import TdmsFile

# === Configuration ===
TDMS_FILE = r'Data\data_file_192.168.137.197_2025-12-18_19-55-27.tdms'  # Path to your TDMS file
TDMS_GROUP = 'Group'        # Name of the group in your TDMS file
SAMPLING_RATE = 1950000     # Sampling rate in Hz (adjust as needed)

# === Load TDMS Data ===
tdms_file = TdmsFile.read(TDMS_FILE)
group = tdms_file[TDMS_GROUP]
channels = [c.name for c in group.channels()]

# Prepare subplots
fig, axes = plt.subplots(1, len(channels), figsize=(12, 5), squeeze=False)

for idx, channel in enumerate(channels):
    data = group[channel][:]
    n = len(data)
    if n == 0:
        print(f"No data found in channel {channel}. Skipping.")
        continue

    # === Perform FFT ===
    frequencies = np.fft.fftfreq(n, d=1/SAMPLING_RATE)
    fft_values = np.fft.fft(data)
    magnitude = np.abs(fft_values)

    # Only keep the positive half of the spectrum
    positive_freqs = frequencies[:n // 2]
    positive_magnitude = magnitude[:n // 2]

    # === Plot FFT ===
    ax = axes[0, idx]
    ax.plot(positive_freqs, positive_magnitude, color='blue', linewidth=0.8)
    ax.set_title(f'FFT of {channel}')
    ax.set_xlim(0, SAMPLING_RATE / 2)
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('Magnitude')
    ax.grid(True)

plt.tight_layout()
plt.show()