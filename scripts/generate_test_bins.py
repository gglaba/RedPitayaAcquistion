#!/usr/bin/env python3
"""
Generate small test BIN files in the Data/ directory.
Files will match the repo's timestamp + CH pattern expected by merge code,
for example: 2025_12_02_12_00_00_CH1.bin
Each file contains interleaved float32 samples: ch0, ch1, ch0, ch1, ...
"""
import os
import struct
from pathlib import Path
import time

DATA_DIR = Path("Data")
DATA_DIR.mkdir(exist_ok=True)

ts = time.strftime("%Y_%m_%d_%H_%M_%S")
# Use a timestamp matching the project's regex YYYY_MM_DD_hh_mm_ss
ts = time.strftime("%Y_%m_%d_%H_%M_%S")

# Create 3 device files following the template: CH1V_CH2V_{timestamp}.bin
# This keeps the "CH<num>" tokens so existing merge code (CH(\d+)) can find channel numbers.
# We'll produce pairs: CH1V_CH2V, CH3V_CH4V, CH5V_CH6V

# Each file will contain interleaved float32 samples for two channels.
ch0 = [0.0, 1.0, 2.0, 3.0]
ch1 = [10.0, 11.0, 12.0, 13.0]

interleaved = []
for a, b in zip(ch0, ch1):
    interleaved.append(a)
    interleaved.append(b)

# pack as little-endian float32
packed = struct.pack('<' + 'f' * len(interleaved), *interleaved)

pairs = [(1,2), (3,4), (5,6)]
for a, b in pairs:
    fname = DATA_DIR / f"CH{a}V_CH{b}V_{ts}.bin"
    with open(fname, 'wb') as f:
        f.write(packed)
    print(f"Wrote {fname} ({len(packed)} bytes)")

print("Test BIN files generated in Data/ using CHxV_CHyV_{timestamp}.bin template")
