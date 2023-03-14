# Developer's notes

Few notes:

- The SCPI server can be run directly by running `pi_server.py`.
- Use the template in `py_server.py` to select which interface handler is to process the query
- New SCPI commands can be added via `add_command`. Just note that the channels tuple corresponds to every segment of the SCPI command (e.g. `GPIO:SOUR:DIG:DATA3?` has 4 segments) and places the channel number of the specified slot in the tuple.
- For debugging, just run the server directly and then send SCPI commands via another computer using debug console commands.
