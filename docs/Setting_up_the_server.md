# Setting up the Raspberry Pi SCPI server

First ensure that the initial [Raspberry Pi setup](Setting_up_the_RPi.md) has been done. Now using the `rc.local` method, the appropriate Python script shall be run on startup to setup the server. First SSH into the Raspberry Pi and run:

```
sudo nano /etc/rc.local
```

Go down to some point just after the comments (that is, before the `exit` command) and enter:

```
python /home/pi/SQDdevRPi/SCPI_Server/pi_server.py
```

noting to modify the directory as appropriate. Now hit `CTRL-X`, `y` and `ENTER` to save the document. After restarting the Raspberry Pi, the SCPI server should be functional.
