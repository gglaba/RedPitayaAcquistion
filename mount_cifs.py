import subprocess
import os

# Configuration
ip_address = 'grzesiulaLenovoIdeaPad'  # IP address of the machine sharing the folder
shared_folder = '/home/grzesiula/Desktop/SignalAcquisitionGUI/Data'  # Path to the shared folder
mount_point = '/mnt/share'  # Mount point on local machine
username = 'grzesiula'  # Username for CIFS share
password = ''  # Password for CIFS share

# Create mount point if it doesn't exist
#if not os.path.exists(mount_point):
 #   os.makedirs(mount_point)

# Prepare the mount command
mount_command = [
    'sudo', 'mount', '-t', 'cifs',
    f'//{ip_address}{shared_folder}',  # CIFS share path
    mount_point,
    '-o', f'username={username},password={password},file_mode=0777,dir_mode=0777'
]

# Execute the mount command
try:
    #subprocess.run(mount_command, check=True)
    print(mount_command)
    print(f'Successfully mounted {shared_folder} at {mount_point}')
except subprocess.CalledProcessError as e:
    print(f'Failed to mount {shared_folder}. Error: {e}')

# Optional: List the contents of the mounted folder
try:
    print("Contents of the mounted folder:")
    #contents = subprocess.run(['ls', mount_point], check=True, stdout=subprocess.PIPE, text=True)
    #print(contents.stdout)
except subprocess.CalledProcessError as e:
    print(f'Failed to list contents of {mount_point}. Error: {e}')
