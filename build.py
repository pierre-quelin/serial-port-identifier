import os
import subprocess
import sys

cmd = [
    sys.executable, '-m', 'PyInstaller',
    '--windowed',
    '--onefile',
    f'--add-data=serial.png{os.pathsep}.',
    '--icon=serial.png',
    'SerialPortIdentifier.py',
]

print(f"Platform: {sys.platform}")
print(f"Command: {' '.join(cmd)}")

subprocess.run(cmd, check=True)
