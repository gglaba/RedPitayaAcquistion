import os
import sys
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
import re
import json
# Adding debugging statements to trace execution and variable values
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# ========= KONFIGURACJA =========
config = json.load(open("live_preview_config.json"))
DATA_DIR = config["DATA_DIR"]
DTYPE = np.int16 if json.load(open(f"./streaming_mode/config.json"))["adc_streaming"]["resolution"] == 16 else np.int8
BYTES_PER_SAMPLE = 2 if DTYPE == np.int16 else 1
SAMPLES_TO_SHOW = config["SAMPLES_TO_SHOW"]   # okno podglądu
UPDATE_INTERVAL_MS = config["UPDATE_INTERVAL_MS"]     # ~33 FPS
DECIMATION = config["DECIMATION"]              # np. 10 jeśli sygnał jest ekstremalnie szybki
SCALE = config["SCALE"]
TDMS_GROUP = config["TDMS_GROUP"]
CHANNELS = config["CHANNELS"]
# ================================


def get_latest_bin_file_for_ip(directory, ip):
    logging.debug(f"Searching for latest .bin file for IP: {ip} in directory: {directory}")
    # Match _<ip>_ in filename to avoid substring collisions
    ip_pattern = re.compile(rf"_{re.escape(ip)}_")
    files = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.endswith(".bin") and ip_pattern.search(f)
    ]
    logging.debug(f"Found files: {files}")
    if not files:
        return None
    return max(files, key=os.path.getmtime)

class LivePlotBin:
    def __init__(self, device_ips):
        logging.debug(f"Initializing LivePlotBin with device IPs: {device_ips}")
        self.device_channel_pairs = [(ip, ch) for ip in device_ips for ch in CHANNELS]
        self.n_plots = len(self.device_channel_pairs)
        self.current_files = [None] * self.n_plots

        self.app = pg.mkQApp("Red Pitaya Live Preview")
        self.win = pg.GraphicsLayoutWidget(title="Live signal preview")
        self.win.resize(1200, 900)

        self.plots = []
        self.curves = []
        for idx, (ip, ch) in enumerate(self.device_channel_pairs):
            row = idx // 2
            col = idx % 2
            plot = self.win.addPlot(row=row, col=col)
            plot.showGrid(x=True, y=True)
            plot.setLabel("left", f"Amplitude {ch} ({ip})")
            plot.setLabel("bottom", "Samples")
            pen = pg.mkPen("y", width=1) if ch == "ch1" else pg.mkPen("c", width=1)
            curve = plot.plot(pen=pen)
            self.plots.append(plot)
            self.curves.append(curve)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(UPDATE_INTERVAL_MS)

        self.win.show()

    def update(self):
        logging.debug("Updating LivePlotBin...")
        for idx, (ip, ch) in enumerate(self.device_channel_pairs):
            logging.debug(f"Processing subplot {idx+1} for IP: {ip}, Channel: {ch}")
            file_path = get_latest_bin_file_for_ip(DATA_DIR, ip)
            logging.debug(f"Latest file path: {file_path}")
            if not file_path:
                self.curves[idx].setData([], [])
                continue

            if file_path != self.current_files[idx]:
                self.current_files[idx] = file_path

            try:
                file_size = os.path.getsize(file_path)
                total_samples = file_size // BYTES_PER_SAMPLE

                if total_samples <= 0:
                    self.curves[idx].setData([], [])
                    continue

                # Assume interleaved channels: ch1, ch2, ch1, ch2, ...
                samples_per_channel = total_samples // len(CHANNELS)
                offset = (samples_per_channel - min(SAMPLES_TO_SHOW, samples_per_channel)) * BYTES_PER_SAMPLE * len(CHANNELS)

                with open(file_path, "rb") as f:
                    f.seek(offset)
                    data = np.fromfile(f, dtype=DTYPE, count=min(SAMPLES_TO_SHOW, samples_per_channel) * len(CHANNELS))

                if data.size == 0:
                    self.curves[idx].setData([], [])
                    continue

                # Extract channel data
                ch_idx = CHANNELS.index(ch)
                channel_data = data[ch_idx::len(CHANNELS)]
                if DECIMATION > 1:
                    channel_data = channel_data[::DECIMATION]

                y = channel_data.astype(np.float32) * SCALE
                x = np.arange(len(y))
                self.plots[idx].setXRange(0, len(y), padding=0)
                self.curves[idx].setData(x, y)
                logging.debug(f"File size: {file_size}, Total samples: {total_samples}")
                logging.debug(f"Channel data size: {channel_data.size}")
            except Exception as e:
                logging.error(f"Error in subplot {idx+1} ({ip}, {ch}): {e}")
                self.curves[idx].setData([], [])

# if __name__ == "__main__":
#     if len(sys.argv) < 2:
#         print("Usage: python live_preview.py <IP1> [<IP2> ...]")
#         sys.exit(1)
#     device_ips = sys.argv[1:]
#     plotter = LivePlotBin(device_ips)
#     pg.exec()


import os
import sys
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
from nptdms import TdmsFile
import re
# ========= KONFIGURACJA =========

# ================================

def get_latest_tdms_file_for_ip(directory, ip):
    logging.debug(f"Searching for latest .tdms file for IP: {ip} in directory: {directory}")
    # Match _<ip>_ in filename to avoid substring collisions
    ip_pattern = re.compile(rf"_{re.escape(ip)}_")
    files = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.endswith(".tdms") and ip_pattern.search(f)
    ]
    logging.debug(f"Found files: {files}")
    if not files:
        return None
    return max(files, key=os.path.getmtime)

class LivePlot:
    def __init__(self, device_ips):
        logging.debug(f"Initializing LivePlot with device IPs: {device_ips}")
        self.device_channel_pairs = [(ip, ch) for ip in device_ips for ch in CHANNELS]
        self.n_plots = len(self.device_channel_pairs)
        self.current_files = [None] * self.n_plots

        self.app = pg.mkQApp("Red Pitaya Live Preview")
        self.win = pg.GraphicsLayoutWidget(title="Live signal preview")
        # Set window size for 3 rows x 2 columns
        self.win.resize(1200, 900)

        self.plots = []
        self.curves = []
        # Arrange plots in 3 rows x 2 columns
        for idx, (ip, ch) in enumerate(self.device_channel_pairs):
            row = idx // 2
            col = idx % 2
            plot = self.win.addPlot(row=row, col=col)
            plot.showGrid(x=True, y=True)
            plot.setLabel("left", f"Amplitude {ch} ({ip})")
            plot.setLabel("bottom", "Samples")
            pen = pg.mkPen("y", width=1) if ch == "ch1" else pg.mkPen("c", width=1)
            curve = plot.plot(pen=pen)
            self.plots.append(plot)
            self.curves.append(curve)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(UPDATE_INTERVAL_MS)

        self.win.show()

    def update(self):
        logging.debug("Updating LivePlot...")
        for idx, (ip, ch) in enumerate(self.device_channel_pairs):
            logging.debug(f"Processing subplot {idx+1} for IP: {ip}, Channel: {ch}")
            file_path = get_latest_tdms_file_for_ip(DATA_DIR, ip)
            logging.debug(f"Latest file path: {file_path}")
            if not file_path:
                self.curves[idx].setData([], [])
                continue

            if file_path != self.current_files[idx]:
                self.current_files[idx] = file_path

            try:
                tdms_file = TdmsFile.read(file_path)
                group_names = [g.name for g in tdms_file.groups()]
                if TDMS_GROUP not in group_names:
                    self.curves[idx].setData([], [])
                    continue
                group = tdms_file[TDMS_GROUP]
                channel_names = [chan.name for chan in group.channels()]
                if ch in channel_names:
                    data = group[ch][:]
                    if DECIMATION > 1:
                        data = data[::DECIMATION]
                    samples_to_read = min(SAMPLES_TO_SHOW, data.size)
                    y = data[-samples_to_read:].astype(np.float32) * SCALE
                    x = np.arange(len(y))
                    self.plots[idx].setXRange(0, len(y), padding=0)
                    self.curves[idx].setData(x, y)
                else:
                    self.curves[idx].setData([], [])
            except Exception as e:
                logging.error(f"Error in subplot {idx+1} ({ip}, {ch}): {e}")

if __name__ == "__main__":
    logging.debug(f"Starting live preview with arguments: {sys.argv}")
    if len(sys.argv) < 3:
        print("Usage: python live_preview.py <bin|tdms> <IP1> [<IP2> ...]")
        sys.exit(1)
    data_format = sys.argv[1].lower()
    device_ips = sys.argv[2:]

    if data_format == "bin":
        plotter = LivePlotBin(device_ips)
    elif data_format == "tdms":
        plotter = LivePlot(device_ips)
    else:
        print("Unknown data format. Use 'bin' or 'tdms'.")
        sys.exit(1)
    pg.exec()