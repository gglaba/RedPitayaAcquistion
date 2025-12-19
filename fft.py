import argparse
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys
import re

# Default configuration
DEFAULT_BIN = r'Data\data_file_192.168.137.197_2025-12-18_19-49-20.bin'
DEFAULT_CHANNEL = 'CH2'
DEFAULT_SAMPLING_RATE = 122000

def detect_total_channels_from_name(bin_file):
    name = Path(bin_file).name
    # match patterns like: _6ch.bin, _6ch_abcd.bin, _6ch-abcd.bin or 6ch anywhere
    m = re.search(r'_(\d+)ch(?=[._-]|$)|(\d+)ch', name, re.IGNORECASE)
    if m:
        # group(1) corresponds to the underscore-prefixed form, group(2) is the fallback
        val = m.group(1) or m.group(2)
        try:
            return int(val)
        except Exception:
            return None
    return None

def parse_channel_arg(channel_arg):
    # Accept "CH1", "ch1", "1"
    if isinstance(channel_arg, int):
        return channel_arg
    s = str(channel_arg).strip()
    m = re.match(r'^(?:ch)?\s*(\d+)$', s, re.IGNORECASE)
    if not m:
        raise ValueError("Invalid channel format. Use 'CH1' or '1'.")
    return int(m.group(1))

def run_fft(bin_file, channel='CH1', sampling_rate=122000, total_channels=None):
    data = np.fromfile(bin_file, dtype=np.float32)
    if data.size == 0:
        raise ValueError(f"No data read from {bin_file}")

    # determine total channels if not provided
    if total_channels is None:
        detected = detect_total_channels_from_name(bin_file)
        if detected is not None:
            total_channels = detected
        else:
            raise ValueError("Total channels could not be determined from filename. "
                             "Provide --channels on the command line.")

    if total_channels < 1:
        raise ValueError("Total channels must be >= 1")

    if data.size % total_channels != 0:
        # Truncate trailing samples so each channel has equal samples
        truncated = data.size - (data.size % total_channels)
        print(f"Warning: total samples ({data.size}) not divisible by channels ({total_channels}). Truncating to {truncated} samples.")
        data = data[:truncated]

    chan_idx = parse_channel_arg(channel) - 1
    if chan_idx < 0 or chan_idx >= total_channels:
        raise ValueError(f"Requested channel {channel} out of range for {total_channels} channels")

    selected_data = data[chan_idx::total_channels]
    n = selected_data.size
    if n == 0:
        raise ValueError("Selected channel contains no samples after slicing")

    fft_values = np.fft.rfft(selected_data)
    frequencies = np.fft.rfftfreq(n, d=1.0 / sampling_rate)
    magnitude = np.abs(fft_values)

    plt.figure(figsize=(10, 6))
    plt.plot(frequencies, magnitude, color='blue', linewidth=0.8)
    #plt.xlim(0, sampling_rate)
    plt.title(f'FFT of {channel} ({Path(bin_file).name})')
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Magnitude')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def main():
    ap = argparse.ArgumentParser(description="Compute FFT for a binary file (interleaved floats).")
    ap.add_argument("--binfile", type=str, default=None, help="Path to .bin file (interleaved floats)")
    ap.add_argument("--channel", type=str, default=DEFAULT_CHANNEL, help="Channel to plot: CH1..CHN or numeric (1..N)")
    ap.add_argument("--samplerate", type=int, default=DEFAULT_SAMPLING_RATE, help="Sampling rate in Hz")
    ap.add_argument("--channels", type=int, default=None, help="Total number of interleaved channels in the file (overrides filename detection)")
    args = ap.parse_args()

    binfile = args.binfile if args.binfile else DEFAULT_BIN
    if not Path(binfile).exists():
        print(f"File not found: {binfile}", file=sys.stderr)
        sys.exit(2)

    try:
        run_fft(binfile, channel=args.channel, sampling_rate=args.samplerate, total_channels=args.channels)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()