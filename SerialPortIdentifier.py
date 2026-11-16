#!/usr/bin/env python3

# Copyright(c) 2022 Pierre Quélin <pierre.quelin.1972@gmail.com>
#
# Author: Pierre Quélin
# Date created: 25/03/2022
# Python Version: 3.13

import os
import re
import sys
import tkinter as tk
from enum import Enum
from pathlib import Path
from threading import Event, Thread
from time import monotonic

from serial import Serial, SerialException
from serial.tools import list_ports

SERIAL_TIMEOUT = 0.3
PING_SIZE = 8
SCAN_PERIOD_MS = 1000
REFRESH_PERIOD_MS = 300
JOIN_TIMEOUT = 1.0


class PortState(Enum):
    ABSENT = ("Not detected", "#ff6b6b")
    READY = ("Connected", "#6fd08c")
    BUSY = ("Unavailable", "#f0a04b")

    def __init__(self, label, color):
        self.label = label
        self.color = color


def resource_path(name):
    """Return the path of a resource, from sources or a PyInstaller build."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / name


def natural_key(text):
    """Sort key so that COM2 comes before COM10."""
    return [int(part) if part.isdigit() else part.lower()
            for part in re.split(r"(\d+)", text)]


class SerialPortProbe:
    """Checks in a background thread whether a loopback is on a port."""

    def __init__(self, dev):
        self._dev = dev
        self._state = PortState.ABSENT
        self._stop = Event()
        self._thread = Thread(target=self._run, daemon=True)
        self._thread.start()

    @property
    def state(self):
        return self._state

    def stop(self):
        self._stop.set()

    def join(self, timeout=None):
        self._thread.join(timeout)

    def _probe(self):
        s = Serial(timeout=SERIAL_TIMEOUT, write_timeout=SERIAL_TIMEOUT)
        s.port = self._dev
        # DTR/RTS must stay low on open, otherwise boards like Arduino reset.
        s.dtr = False
        s.rts = False
        try:
            s.open()
        except (SerialException, OSError):
            return PortState.BUSY

        try:
            with s:
                s.reset_input_buffer()
                ping = os.urandom(PING_SIZE)
                s.write(ping)
                pong = s.read(len(ping))
        except (SerialException, OSError):
            return PortState.ABSENT
        return PortState.READY if pong == ping else PortState.ABSENT

    def _run(self):
        while not self._stop.is_set():
            start = monotonic()
            self._state = self._probe()
            self._stop.wait(max(0.0, SERIAL_TIMEOUT - (monotonic() - start)))


class PortCard(tk.Frame):
    def __init__(self, master, dev, desc):
        super().__init__(master, padx=14, pady=10, relief="groove", bd=1)
        self.columnconfigure(1, weight=1)

        self._led = tk.Label(self, text="●", font=("", 16))
        self._led.grid(row=0, column=0, rowspan=2, padx=(0, 12))

        tk.Label(self, text=dev, font=("", 11, "bold"), anchor="w").grid(
            row=0, column=1, sticky="w")
        self._desc = tk.Label(self, text=desc, anchor="w")
        self._desc.grid(row=1, column=1, sticky="w")

        self._status = tk.Label(self, font=("", 10, "bold"))
        self._status.grid(row=0, column=2, rowspan=2, sticky="e", padx=(20, 0))

        self._state = None
        self.set_state(PortState.ABSENT)

    def set_description(self, desc):
        if self._desc.cget("text") != desc:
            self._desc.config(text=desc)

    def set_state(self, state):
        if state == self._state:
            return
        self._state = state
        self._led.config(fg=state.color)
        self._status.config(text=state.label, fg=state.color)


class MainApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Serial Port Identifier")
        self.resizable(False, False)
        self._set_icon()

        self._ports = {}  # dev -> (SerialPortProbe, PortCard)
        self._order = []
        self._scan_id = None
        self._refresh_id = None

        self._create_widgets()
        self._scan()
        self._refresh_states()

    def _set_icon(self):
        try:
            # Keep a reference, otherwise the image is garbage collected.
            self._icon = tk.PhotoImage(file=resource_path("serial.png"))
        except tk.TclError:
            return
        self.iconphoto(True, self._icon)

    def _create_widgets(self):
        self._subtitle = tk.Label(self, text="", font=("", 9))
        self._subtitle.pack(anchor="w", padx=20, pady=(18, 10))

        self._container = tk.Frame(self)
        self._container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self._empty = tk.Label(
            self._container,
            text="Plug in a serial port or a USB-serial adapter…",
            font=("", 10), pady=30)

    def _scan(self):
        """Detect added or removed ports."""
        current = {p.device: p.description for p in list_ports.comports()}

        for dev in list(self._ports):
            if dev not in current:
                probe, card = self._ports.pop(dev)
                probe.stop()
                card.destroy()

        for dev, desc in current.items():
            if dev in self._ports:
                self._ports[dev][1].set_description(desc)
            else:
                self._ports[dev] = (SerialPortProbe(dev),
                                    PortCard(self._container, dev, desc))

        self._layout_cards()
        self._update_header()
        self._scan_id = self.after(SCAN_PERIOD_MS, self._scan)

    def _layout_cards(self):
        order = sorted(self._ports, key=natural_key)
        if order == self._order:
            return
        self._order = order
        for dev in order:
            self._ports[dev][1].pack_forget()
        for dev in order:
            self._ports[dev][1].pack(fill="x", pady=4)

    def _refresh_states(self):
        """Update the LEDs from the probes' states."""
        for probe, card in self._ports.values():
            card.set_state(probe.state)
        self._refresh_id = self.after(REFRESH_PERIOD_MS, self._refresh_states)

    def _update_header(self):
        count = len(self._ports)
        self._subtitle.config(text=f"{count} port(s) detected" if count
                              else "No port detected")
        if count:
            self._empty.pack_forget()
        elif not self._empty.winfo_manager():
            self._empty.pack()

    def destroy(self):
        for after_id in (self._scan_id, self._refresh_id):
            if after_id is not None:
                self.after_cancel(after_id)

        probes = [probe for probe, _card in self._ports.values()]
        for probe in probes:
            probe.stop()
        for probe in probes:
            probe.join(JOIN_TIMEOUT)
        super().destroy()


if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()
