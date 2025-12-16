import os
import re

def parse_footer(log_path):
    with open(log_path, "r") as f:
        text = f.read()

    patt = r"FOOTER:\s+samples_per_channel = (\d+)\s+channels\s+= (\d+)\s+bytes_per_sample\s+= (\d+)\s+expected_file_size\s+= (\d+)"
    m = re.search(patt, text)
    if not m:
        raise ValueError("Footer not found in log")

    samples = int(m.group(1))
    channels = int(m.group(2))
    bytes_per_sample = int(m.group(3))
    expected_size = int(m.group(4))

    return samples, channels, bytes_per_sample, expected_size

def validate(bin_path, log_path):
    samples, ch, bps, expected = parse_footer(log_path)
    actual = os.path.getsize(bin_path)

    if actual == expected:
        print("OK — plik poprawny.")
    else:
        print("BŁĄD — plik niekompletny lub uszkodzony.")
        print("expected:", expected)
        print("actual  :", actual)

# Użycie:
#validate("Data\CH3V_CH4V_2025_12_11_12_10_00.bin", "logs/debug_rp-f0ba38_local.log")
