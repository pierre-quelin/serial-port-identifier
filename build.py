import sys
import subprocess

# Determines the separator based on the platform
sep = ';' if sys.platform == 'win32' else ':'

# Builds the PyInstaller command
cmd = [
    'pyinstaller',
    '--windowed',
    '--onefile',
    f'--add-binary=serial.png{sep}.',
    'SerialPortIdentifier.py'
]

print(f"Plateforme: {sys.platform}")
print(f"Séparateur: {sep}")
print(f"Commande: {' '.join(cmd)}")

# Execute the command
result = subprocess.run(cmd, check=True)
sys.exit(result.returncode)
