#!/usr/bin/env python3
import argparse, numpy as np, matplotlib.pyplot as plt, re
from pathlib import Path

def split_channels(data):
    """Zwraca słownik {CH1: ndarray, CH2: …} dla 2/4/6/… kanałów."""
    if data.size % 2:
        raise ValueError("Nieparzysta liczba floatów – zły plik?")
    n_chan = 2
    while data.size % n_chan == 0 and n_chan <= 32:
        n_chan *= 2
    n_chan //= 2
    n_chan = 4
    chans = {f"CH{i+1}": data[i::n_chan] for i in range(n_chan)}
    
    return chans

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Podgląd .bin Red Pitayi (2-/4-/6-kanał).")
    ap.add_argument("binfile", type=Path)
    ap.add_argument("--chan", default="all", help="np. CH1, CH3, all")
    ap.add_argument("--max", type=int, help="Ogranicz liczbę próbek")
    args = ap.parse_args()

    data = np.memmap(args.binfile, dtype=np.float32, mode='r')
    chans = split_channels(data)

    if args.chan != "all":
        to_plot = {args.chan: chans[args.chan]}
    else:
        to_plot = chans

    if args.max:
        to_plot = {k: v[:args.max] for k, v in to_plot.items()}

    plt.figure(figsize=(10, 5))
    for k, v in to_plot.items():
        plt.plot(v, label=k)
    plt.title(args.binfile.name)
    plt.xlabel("Próbka"); plt.ylabel("Napięcie [V]")
    plt.grid(alpha=.3); plt.legend(); plt.tight_layout(); plt.show()
