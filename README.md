# Raspberry Pi interfacing with SQDToolz

Certain devices in the lab are interfaced with the Raspberry Pi. For example:

- Several microwave sources converted from the USB-Serial interface into Ethernet
- Using GPIO pins to slowly toggle states on a electro-mechanical switch

There is an implementation using [SSH](scripts/README.md) and the `paramiko` module. However, this has issues when running in an IPython notebook. Therefore, the recommended approach is to run a SCPI-compatible server via a TCP-socket through which clients communicate via SCPI commands. The following documentation is relevant:

- [Initial setup on the Raspberry Pi](docs/Setting_up_the_RPi.md)
- [Setting up the Raspberry Pi SCPI server](docs/Setting_up_the_server.md)
- [Developer's Notes](docs/DevNotes.md)
