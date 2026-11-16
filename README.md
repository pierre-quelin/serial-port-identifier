# Serial Port Identifier
Program to easily list and physically identify all serial ports installed on a computer.

## Usage

* Build a loopback dongle with a basic DB9 connector and join only pins 2 (Rx) and 3 (Tx) together.
* Disconnect all serial port connectors from the PC.
* Connect your dongle alternately to all ports (built-in ports or USB-serial adapters).
* The LED of the port the dongle is plugged into turns green ("Connected").
* Enjoy ;-)

Port states:

* **Connected** (green): the loopback dongle is detected.
* **Not detected** (red): the port is free but nothing echoes back.
* **Unavailable** (orange): the port cannot be opened, usually because another application uses it.

> **Warning:** the program periodically opens every serial port and writes a few random bytes to it.
> DTR and RTS are kept low to avoid resetting boards such as Arduino, but avoid running it while
> real equipment (modem, PLC, ...) is connected.

## Creation of a standalone executable in order not to have to install python on the target.

### Create a virtual environment

Linux:

```shell
me@mypc:~/workspace/SerialPortIdentifier$ python3 -m venv .venv
me@mypc:~/workspace/SerialPortIdentifier$ source .venv/bin/activate
(.venv) me@mypc:~/workspace/SerialPortIdentifier$ pip install -r requirements-build.txt
```

Windows (PowerShell):

```powershell
PS C:\workspace\SerialPortIdentifier> python -m venv .venv
PS C:\workspace\SerialPortIdentifier> .\.venv\Scripts\Activate.ps1
(.venv) PS C:\workspace\SerialPortIdentifier> pip install -r requirements-build.txt
```

### Build

```shell
(.venv) me@mypc:~/workspace/SerialPortIdentifier$ python build.py
```

The executable is generated in the `dist/` directory.
