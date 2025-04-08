import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# === CONFIGURATION ===
DECIMATION = 65536
BASE_SAMPLE_RATE = 125_000_000
CSV_FILE = r'Data\CH3V_CH4V_2025_04_01_20_16_28.csv'
COLUMN_NAME = 'CH3V'  # Use 'CH1V' or 'CH2V'
DOWNSAMPLE_STEP = 1
JUMP_THRESHOLD_VOLT = 10

# === Load Data ===
df = pd.read_csv(CSV_FILE, usecols=[COLUMN_NAME])
df[COLUMN_NAME] = pd.to_numeric(df[COLUMN_NAME], errors='coerce')
df.dropna(subset=[COLUMN_NAME], inplace=True)

sygnal = df[COLUMN_NAME].reset_index(drop=True)

# === Time axis ===
sample_rate = BASE_SAMPLE_RATE / DECIMATION
dt = 1.0 / sample_rate
czas = np.arange(len(sygnal)) * dt

# === Downsample ===
sygnal_down = sygnal.iloc[::DOWNSAMPLE_STEP].reset_index(drop=True)
czas_down = czas[::DOWNSAMPLE_STEP]

# Detect jumps
diff = np.abs(np.diff(sygnal_down))
discontinuities = np.where(diff > JUMP_THRESHOLD_VOLT)[0]

# Convert Series to list so we can insert NaNs
sygnal_clean = sygnal_down.tolist()
czas_clean = list(czas_down)

# Insert NaNs at detected discontinuities
for idx in reversed(discontinuities):
    sygnal_clean.insert(idx + 1, np.nan)
    czas_clean.insert(idx + 1, czas_clean[idx])  # duplicate time for consistency

# === Plot ===
plt.figure(figsize=(10, 5))
plt.plot(czas_clean, sygnal_clean)
plt.xlabel("Czas (s)")
plt.ylabel(f"Napięcie ({COLUMN_NAME}) [V]")
plt.title(f"Sygnał {COLUMN_NAME} – {sample_rate:.1f} Hz próbkowanie")
plt.grid(True)
plt.tight_layout()
plt.show()
