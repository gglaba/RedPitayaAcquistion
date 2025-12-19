import os
import sys
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
import re
import json
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
    # Match _<ip>_ in filename to avoid substring collisions
    ip_pattern = re.compile(rf"_{re.escape(ip)}_")
    files = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.endswith(".bin") and ip_pattern.search(f)
    ]
    if not files:
        return None
    return max(files, key=os.path.getmtime)

class LivePlotBin:
    def __init__(self, device_ips):
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
        for idx, (ip, ch) in enumerate(self.device_channel_pairs):
            file_path = get_latest_bin_file_for_ip(DATA_DIR, ip)
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

            except Exception as e:
                print(f"Błąd w subplot {idx+1} ({ip}, {ch}):", e)
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
    # Match _<ip>_ in filename to avoid substring collisions
    ip_pattern = re.compile(rf"_{re.escape(ip)}_")
    files = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.endswith(".tdms") and ip_pattern.search(f)
    ]
    if not files:
        return None
    return max(files, key=os.path.getmtime)

class LivePlot:
    def __init__(self, device_ips):
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
        for idx, (ip, ch) in enumerate(self.device_channel_pairs):
            file_path = get_latest_tdms_file_for_ip(DATA_DIR, ip)
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
                print(f"Błąd w subplot {idx+1} ({ip}, {ch}):", e)

if __name__ == "__main__":
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





# import os
# import time
# import numpy as np
# import pyqtgraph as pg
# from pyqtgraph.Qt import QtCore

# # ========= KONFIGURACJA =========
# DATA_DIR = "Data"
# DTYPE = np.int16
# BYTES_PER_SAMPLE = 2

# SAMPLES_TO_SHOW = 40000   # okno podglądu
# UPDATE_INTERVAL_MS = 30     # ~33 FPS
# DECIMATION = 1              # np. 10 jeśli sygnał jest ekstremalnie szybki
# SCALE = 1.0
# # ================================


# def get_newest_bin_file(directory):
#     files = [
#         os.path.join(directory, f)
#         for f in os.listdir(directory)
#         if f.endswith(".bin")
#     ]
#     if not files:
#         return None
#     return max(files, key=os.path.getmtime)


# class LivePlotBin:
#     def __init__(self):
#         self.current_file = None

#         self.app = pg.mkQApp("Red Pitaya Live Preview")
#         self.win = pg.GraphicsLayoutWidget(title="Live signal preview")
#         self.win.resize(1200, 600)

#         self.plot = self.win.addPlot()
#         self.plot.showGrid(x=True, y=True)
#         self.plot.setLabel("left", "Amplitude")
#         self.plot.setLabel("bottom", "Samples")
        

#         self.curve = self.plot.plot(pen=pg.mkPen("y", width=1))

#         self.timer = QtCore.QTimer()
#         self.timer.timeout.connect(self.update)
#         self.timer.start(UPDATE_INTERVAL_MS)

#         self.win.show()

#     def update(self):
#         newest_file = get_newest_bin_file(DATA_DIR)

#         if newest_file is None:
#             return

#         if newest_file != self.current_file:
#             print(f"Nowy plik: {newest_file}")
#             self.current_file = newest_file

#         try:
#             file_size = os.path.getsize(self.current_file)
#             total_samples = file_size // BYTES_PER_SAMPLE

#             if total_samples <= 0:
#                 return

#             samples_to_read = min(SAMPLES_TO_SHOW, total_samples)
#             offset = (total_samples - samples_to_read) * BYTES_PER_SAMPLE

#             with open(self.current_file, "rb") as f:
#                 f.seek(offset)
#                 data = np.fromfile(f, dtype=DTYPE, count=samples_to_read)

#             if data.size == 0:
#                 return

#             if DECIMATION > 1:
#                 data = data[::DECIMATION]

#             y = data.astype(np.float32) * SCALE
#             x = np.arange(len(y))
#             self.plot.setXRange(0, 10000, padding=0)

#             self.curve.setData(x, y)

#         except Exception as e:
#             print("Błąd:", e)

# if __name__ == "__main__":
#     plotter = LivePlotBin()   # ← WAŻNE: referencja!
#     pg.exec()      






######DZIALA DLA TDMS

# import os
# import numpy as np
# import pyqtgraph as pg
# from pyqtgraph.Qt import QtCore
# from nptdms import TdmsFile  # Dodane

# # ========= KONFIGURACJA =========
# DATA_DIR = "Data"
# SAMPLES_TO_SHOW = 40000
# UPDATE_INTERVAL_MS = 30
# DECIMATION = 1
# SCALE = 1.0
# TDMS_GROUP = "Group"     # <- Zmień na odpowiednią grupę
# TDMS_CHANNEL = "ch1" # <- Zmień na odpowiedni kanał
# # ================================

# def get_newest_tdms_file(directory):
#     files = [
#         os.path.join(directory, f)
#         for f in os.listdir(directory)
#         if f.endswith(".tdms")
#     ]
#     if not files:
#         return None
#     return max(files, key=os.path.getmtime)

# class LivePlot:
#     def __init__(self):
#         self.current_file = None

#         self.app = pg.mkQApp("Red Pitaya Live Preview")
#         self.win = pg.GraphicsLayoutWidget(title="Live signal preview")
#         self.win.resize(1200, 600)

#         self.plot = self.win.addPlot()
#         self.plot.showGrid(x=True, y=True)
#         self.plot.setLabel("left", "Amplitude")
#         self.plot.setLabel("bottom", "Samples")

#         self.curve = self.plot.plot(pen=pg.mkPen("y", width=1))

#         self.timer = QtCore.QTimer()
#         self.timer.timeout.connect(self.update)
#         self.timer.start(UPDATE_INTERVAL_MS)

#         self.win.show()

#     def update(self):
#         newest_file = get_newest_tdms_file(DATA_DIR)

#         if newest_file is None:
#             return

#         if newest_file != self.current_file:
#             print(f"Nowy plik: {newest_file}")
#             self.current_file = newest_file

#         try:
#             tdms_file = TdmsFile.read(self.current_file)
#             print("Groups:",[g.name for g in tdms_file.groups()])
#             for group in tdms_file.groups():
#                 print("Channels in", group.name, ":", [ch.name for ch in group.channels()])
#             group = tdms_file[TDMS_GROUP]
#             channel = group[TDMS_CHANNEL]
#             data = channel[:]

#             if data.size == 0:
#                 return

#             if DECIMATION > 1:
#                 data = data[::DECIMATION]

#             samples_to_read = min(SAMPLES_TO_SHOW, data.size)
#             y = data[-samples_to_read:].astype(np.float32) * SCALE
#             x = np.arange(len(y))
#             self.plot.setXRange(0, 10000, padding=0)

#             self.curve.setData(x, y)

#         except Exception as e:
#             print("Błąd:", e)

# if __name__ == "__main__":
#     plotter = LivePlot()
#     pg.exec()


# import os
# import numpy as np
# import pyqtgraph as pg
# from pyqtgraph.Qt import QtCore
# from nptdms import TdmsFile  # Dodane

# # ========= KONFIGURACJA =========
# DATA_DIR = "Data"
# SAMPLES_TO_SHOW = 40000
# UPDATE_INTERVAL_MS = 30
# DECIMATION = 1
# SCALE = 1.0
# TDMS_GROUP = "Group"     # <- Zmień na odpowiednią grupę
# TDMS_CHANNEL = "ch1" # <- Zmień na odpowiedni kanał
# # ================================

# def get_newest_tdms_file(directory):
#     files = [
#         os.path.join(directory, f)
#         for f in os.listdir(directory)
#         if f.endswith(".tdms")
#     ]
#     if not files:
#         return None
#     return max(files, key=os.path.getmtime)

# class LivePlot:
#     def __init__(self):
#         self.current_file = None

#         self.app = pg.mkQApp("Red Pitaya Live Preview")
#         self.win = pg.GraphicsLayoutWidget(title="Live signal preview")
#         self.win.resize(1200, 600)

#         # Plot for ch1
#         self.plot1 = self.win.addPlot(row=0, col=0)
#         self.plot1.showGrid(x=True, y=True)
#         self.plot1.setLabel("left", "Amplitude ch1")
#         self.plot1.setLabel("bottom", "Samples")
#         self.curve1 = self.plot1.plot(pen=pg.mkPen("y", width=1))

#         # Plot for ch2
#         self.plot2 = self.win.addPlot(row=1, col=0)
#         self.plot2.showGrid(x=True, y=True)
#         self.plot2.setLabel("left", "Amplitude ch2")
#         self.plot2.setLabel("bottom", "Samples")
#         self.curve2 = self.plot2.plot(pen=pg.mkPen("c", width=1))

#         self.timer = QtCore.QTimer()
#         self.timer.timeout.connect(self.update)
#         self.timer.start(UPDATE_INTERVAL_MS)

#         self.win.show()

#     def update(self):
#         newest_file = get_newest_tdms_file(DATA_DIR)

#         if newest_file is None:
#             return

#         if newest_file != self.current_file:
#             print(f"Nowy plik: {newest_file}")
#             self.current_file = newest_file

#         try:
#             tdms_file = TdmsFile.read(self.current_file)
#             group = tdms_file[TDMS_GROUP]

#             # ch1
#             channel1 = group["ch1"]
#             data1 = channel1[:]
#             if DECIMATION > 1:
#                 data1 = data1[::DECIMATION]
#             samples_to_read1 = min(SAMPLES_TO_SHOW, data1.size)
#             y1 = data1[-samples_to_read1:].astype(np.float32) * SCALE
#             x1 = np.arange(len(y1))
#             self.plot1.setXRange(0, len(y1), padding=0)
#             self.curve1.setData(x1, y1)

#             # ch2
#             channel2 = group["ch2"]
#             data2 = channel2[:]
#             if DECIMATION > 1:
#                 data2 = data2[::DECIMATION]
#             samples_to_read2 = min(SAMPLES_TO_SHOW, data2.size)
#             y2 = data2[-samples_to_read2:].astype(np.float32) * SCALE
#             x2 = np.arange(len(y2))
#             self.plot2.setXRange(0, len(y2), padding=0)
#             self.curve2.setData(x2, y2)

#         except Exception as e:
#             print("Błąd:", e)

# if __name__ == "__main__":
#     plotter = LivePlot()
#     pg.exec()

####DZIALA NA MULTIPLE IP
# import os
# import sys
# import numpy as np
# import pyqtgraph as pg
# from pyqtgraph.Qt import QtCore
# from nptdms import TdmsFile
# import re
# # ========= KONFIGURACJA =========
# DATA_DIR = "Data"
# SAMPLES_TO_SHOW = 40000
# UPDATE_INTERVAL_MS = 100
# DECIMATION = 1
# SCALE = 20.0
# TDMS_GROUP = "Group"
# CHANNELS = ["ch1", "ch2"]
# # ================================

# def get_latest_tdms_file_for_ip(directory, ip):
#     # Match _<ip>_ in filename to avoid substring collisions
#     ip_pattern = re.compile(rf"_{re.escape(ip)}_")
#     files = [
#         os.path.join(directory, f)
#         for f in os.listdir(directory)
#         if f.endswith(".tdms") and ip_pattern.search(f)
#     ]
#     if not files:
#         return None
#     return max(files, key=os.path.getmtime)

# class LivePlot:
#     def __init__(self, device_ips):
#         self.device_channel_pairs = [(ip, ch) for ip in device_ips for ch in CHANNELS]
#         self.n_plots = len(self.device_channel_pairs)
#         self.current_files = [None] * self.n_plots

#         self.app = pg.mkQApp("Red Pitaya Live Preview")
#         self.win = pg.GraphicsLayoutWidget(title="Live signal preview")
#         self.win.resize(1200, 300 * self.n_plots)

#         self.plots = []
#         self.curves = []
#         for idx, (ip, ch) in enumerate(self.device_channel_pairs):
#             plot = self.win.addPlot(row=idx, col=0)
#             plot.showGrid(x=True, y=True)
#             plot.setLabel("left", f"Amplitude {ch} ({ip})")
#             plot.setLabel("bottom", "Samples")
#             pen = pg.mkPen("y", width=1) if ch == "ch1" else pg.mkPen("c", width=1)
#             curve = plot.plot(pen=pen)
#             self.plots.append(plot)
#             self.curves.append(curve)

#         self.timer = QtCore.QTimer()
#         self.timer.timeout.connect(self.update)
#         self.timer.start(UPDATE_INTERVAL_MS)

#         self.win.show()

#     def update(self):
#         for idx, (ip, ch) in enumerate(self.device_channel_pairs):
#             file_path = get_latest_tdms_file_for_ip(DATA_DIR, ip)
#             if not file_path:
#                 self.curves[idx].setData([], [])
#                 continue

#             if file_path != self.current_files[idx]:
#                 self.current_files[idx] = file_path

#             try:
#                 tdms_file = TdmsFile.read(file_path)
#                 group_names = [g.name for g in tdms_file.groups()]
#                 if TDMS_GROUP not in group_names:
#                     self.curves[idx].setData([], [])
#                     continue
#                 group = tdms_file[TDMS_GROUP]
#                 channel_names = [chan.name for chan in group.channels()]
#                 if ch in channel_names:
#                     data = group[ch][:]
#                     if DECIMATION > 1:
#                         data = data[::DECIMATION]
#                     samples_to_read = min(SAMPLES_TO_SHOW, data.size)
#                     y = data[-samples_to_read:].astype(np.float32) * SCALE
#                     x = np.arange(len(y))
#                     self.plots[idx].setXRange(0, len(y), padding=0)
#                     self.curves[idx].setData(x, y)
#                 else:
#                     self.curves[idx].setData([], [])
#             except Exception as e:
#                 print(f"Błąd w subplot {idx+1} ({ip}, {ch}):", e)

# if __name__ == "__main__":
#     if len(sys.argv) < 2:
#         print("Usage: python live_preview.py <IP1> [<IP2> ...]")
#         sys.exit(1)
#     device_ips = sys.argv[1:]
#     plotter = LivePlot(device_ips)
#     pg.exec()

