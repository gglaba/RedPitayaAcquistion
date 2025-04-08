import pandas as pd
import matplotlib.pyplot as plt

# === Configuration ===
CSV_FILE = r'Data/2025_04_08_18_39_22_merged.csv'  # Path to your CSV file
COLUMN_X = 'CH3V'   # Column for X-axis
COLUMN_Y = 'CH4V'  # Column for Y-axis
COLUMN_Z = 'CH1V'
COLUMN_W = 'CH2V'
# === Load Data ===
# Read the CSV file
data = pd.read_csv(CSV_FILE)

# Ensure the columns exist in the file
if COLUMN_X not in data.columns or COLUMN_Y not in data.columns or COLUMN_Z not in data.columns or COLUMN_W not in data.columns:
    raise ValueError(f"Columns '{COLUMN_X}' and '{COLUMN_Y}' not found in the file.")

# Extract the columns
x = data[COLUMN_X]
y = data[COLUMN_Y]
z = data[COLUMN_Z]
w = data[COLUMN_W]

# === Plot Data ===
plt.figure(figsize=(10, 6))

# Plot CH1V (X-axis) with one color
plt.plot(w, label=COLUMN_W, color='blue', marker='o', linestyle='', markersize=2)

# Plot CH2V (Y-axis) with another color
plt.plot(y, label=COLUMN_Y, color='red', marker='x', linestyle='-', markersize=2)

plt.title('XY Plot with Different Colors')
plt.xlabel('Index')
plt.ylabel('Values')
plt.grid(True)
plt.legend()
plt.tight_layout()

# Show the plot
plt.show()