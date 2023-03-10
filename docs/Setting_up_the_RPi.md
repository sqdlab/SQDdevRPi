# Setting up the Raspberry Pi

Format a Micro-SD card using [Raspberry Pi Imaging Tool](https://www.raspberrypi.com/software/). Before writing the image ensure the following:

- As of April 2022 a password needs to be set using the imager tool - make sure to set the username as well
- Enable SSH (it is easier than doing it later via the boot drive of the SD card)

Upon inserting the SD card, the Raspberry Pi should boot and automatically connect to the LAN:

- If no external monitor is available, just check the router logs for the new dynamic IP on the lab network.
- Use any SSH client (like PuTTy) via the IP address and the credentials entered in the beginning into the imaging tool.

Upon connecting via SSH, remain in the home directory and run the command:

```
git clone https://github.com/sqdlab/SQDdevRPi.git
```

This should have the files in the standardised directory for *SQDToolz*.


## Setting up Serial capability

The `pyserial` package should already be installed (using basic raspberry Pi OS).

## Setting up GPIO capability

SSH into the Raspberry Pi and run:

```
sudo apt-get install rpi.gpio
```

Now to ensure that the [GPIO pins have an appropriate state during startup](https://www.raspberrypi.com/documentation/computers/config_txt.html#gpio-control):

- Shut down the Raspberry Pi, pull the SD card out and view it on a PC (in Windows, the boot partition should be readable)
- Locate and open `config.txt`
- To place a GPIO pin (for example, GPIO2) into a low output state, add the line:
    ```
    gpio=2=op,dl
    ```
- To place a GPIO pin (for example, GPIO2) into a high output state, add the line:
    ```
    gpio=2=op,dh
    ```
- Save the file and reinsert SD card back into the Raspberry Pi

Note that certain multipurpose GPIO pins like the RX-UART pin will require further bootloader switches. In this case, SSH into the Raspberry Pi and [run](https://www.raspberrypi.com/documentation/computers/configuration.html):

```
sudo raspi-config
```

Then follow the instructions to disable features such as UART on startup.
