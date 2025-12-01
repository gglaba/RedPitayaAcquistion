import os
import re
import numpy as np
from pathlib import Path
from collections import defaultdict
import shutil
import gc
import time

def merge_bin_files():


    data_dir = Path("Data")
    merged_dir = Path("Merged")
    archive_dir = Path("Archive")


    merged_dir.mkdir(exist_ok=True)
    archive_dir.mkdir(exist_ok=True)


    bin_files = [f for f in data_dir.glob("*.bin")]
    if not bin_files:
        print("No binary files found in Data directory")
        return


    ts_pattern = re.compile(r"\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}")
    grouped_files = defaultdict(list)

    for file in bin_files:
        ts_match = ts_pattern.search(file.name)
        if ts_match:
            grouped_files[ts_match.group(0)].append(file)


    for timestamp, files in grouped_files.items():
        if len(files) > 3:
            print(f"Warning: More than 3 files found for timestamp {timestamp}. Using first 3 only.")
            files = files[:3]
        elif len(files) < 2:
            print(f"Skipping timestamp {timestamp}: Need at least 2 files to merge")
            continue

        memmaps = []
        try:

            ch_pattern = re.compile(r"CH(\d+)", re.IGNORECASE)
            files.sort(key=lambda f: int(ch_pattern.search(f.name).group(1)))

            for f in files:
                try:
                    mm = np.memmap(f, dtype=np.float32, mode="r")
                    memmaps.append(mm)
                except Exception as e:
                    print(f"Error memory-mapping file {f}: {str(e)}")

                    for opened_mm in memmaps:
                        opened_mm._mmap.close()
                    raise


            sizes = [m.size for m in memmaps]
            min_size = min(sizes)
            
            if len(set(sizes)) != 1:
                print(f"Warning: Unequal sample counts {sizes} for {timestamp} - truncating to {min_size}")
                views = [m[:min_size] for m in memmaps]
            else:
                views = memmaps


            samples_per_chan = min_size // 2
            n_devices = len(views)
            total_channels = n_devices * 2


            merged = np.empty(samples_per_chan * total_channels, dtype=np.float32)
            
            for dev_idx, mm in enumerate(views):
                merged[dev_idx*2 :: total_channels] = mm[0::2]
                merged[dev_idx*2+1 :: total_channels] = mm[1::2]


            merged_name = f"{timestamp}_{total_channels}ch.bin"
            merged_path = merged_dir / merged_name
            merged.tofile(merged_path)
            print(f"Created merged file: {merged_name}")


            for mm in memmaps:
                mm._mmap.close()
                del mm
            

            gc.collect()


            for file in files:
                max_retries = 3
                retry_count = 0
                while retry_count < max_retries:
                    try:
                        archive_path = archive_dir / file.name
                        shutil.move(str(file), str(archive_path))
                        print(f"Moved {file.name} to archive")
                        break
                    except PermissionError:
                        retry_count += 1
                        if retry_count == max_retries:
                            raise
                        print(f"Retrying move operation for {file.name}")
                        time.sleep(0.5)

        except Exception as e:
            print(f"Error processing timestamp {timestamp}: {str(e)}")

            for mm in memmaps:
                try:
                    mm._mmap.close()
                except:
                    pass
            gc.collect()
            continue

if __name__ == "__main__":
    merge_bin_files()