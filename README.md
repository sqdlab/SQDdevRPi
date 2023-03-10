# Raspberry Pi interfacing with SQDToolz

Certain devices in the lab are interfaced with the Raspberry Pi. For example:

- Several microwave sources converted from the USB-Serial interface into Ethernet
- Using GPIO pins to slowly toggle states on a electro-mechanical switch

The scheme uses Python scripts that run on the Raspberry Pi. There is a **console interface** that one may access via **SSH**. *SQDToolz* uses this interface to communicate with the Raspberry Pi via the `paramiko` library. To use the library, consult the documentation:

- [Setting up the Raspberry Pi](docs/Setting_up_the_RPi.md)
- Available scripts:
    - GPIO interface
    - Windfreak serial interface
