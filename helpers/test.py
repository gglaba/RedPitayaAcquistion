from nptdms import TdmsFile
import matplotlib.pyplot as plt
import numpy as np

# Ścieżka do pliku TDMS
def plottdms():
    tdms_path = "data_file_192.168.137.19_2025-12-16_14-54-22.tdms"

    # Wczytanie pliku
    tdms_file = TdmsFile.read(tdms_path)
    print(tdms_file.properties)

    # Wypisanie dostępnych grup i kanałów
    print("Dostępne grupy i kanały:")
    for group in tdms_file.groups():
        print(f"Grupa: {group.name}")
        for channel in group.channels():
            print(f"  Kanał: {channel.name}")

    # ===== WYBÓR DANYCH =====
    group_name = tdms_file.groups()[0].name      # pierwsza grupa
    channel_name = tdms_file[group_name].channels()[0].name  # pierwszy kanał

    channel = tdms_file[group_name][channel_name]
    data = channel[:]

    # --- ADC to Volts conversion ---
    # Red Pitaya: 16-bit ADC, ±1V or ±10V range (check your acquisition settings!)
    # If ±1V range:
    input_range =1.0  # Change to 10.0 if you used ±10V range
    max_adc = 32768    # 16-bit signed
    data_volts = data * (input_range / max_adc)


    # Oś X (jeśli brak czasu w metadanych)
    x = np.arange(len(data))

    # Plot
    plt.figure()
    plt.plot(x, data_volts)
    plt.xlabel("Próbka")
    plt.ylabel("Napięcie [V]")
    plt.title(f"{group_name} / {channel_name}")
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    # Example usage
    plottdms()