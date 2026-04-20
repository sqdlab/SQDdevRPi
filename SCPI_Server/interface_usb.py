import serial
import serial.tools.list_ports

from scpi_base import SCPIBase
from scpi_event import SCPIDeviceError, SCPIQueryError

def dict_from_strings(strings):
    ''' take a list of key:value pairs and return them as a dictionary '''
    return dict([s.strip() for s in kv.split(':', 1)] for kv in strings if ':' in kv)

class PiUSB(SCPIBase):
    _REVISION = 1

    def __init__(self, timeout=0.9, debugging=False):
        super(PiUSB, self).__init__()
        max_alias = 999
        self.debugging = debugging
        if self.debugging: print("Debugging mode Active")
        

        # get a list of serial objects, indexed by port name (i.e. '/dev/ttyACM0')
        self.ports = {}
        self.aliases = {}
        index = 1
        for port in serial.tools.list_ports.comports():
            ser = serial.Serial(port.device, timeout=timeout, write_timeout=timeout)
            # wipe input and output buffer in from the last time this device was operated
            ser.reset_input_buffer()
            ser.reset_output_buffer()

            self.ports[port.device] = (ser, port.manufacturer)
            self.aliases[index] = port.device
            index += 1

        # add commands to the SCPI parser
        self.add_command('USB:DEVices', getter=self.list_devices)
        self.add_command('USB:ALIas',   setter=self.assign_alias,   channels=(None, max_alias))
        self.add_command('USB:WRIte',   setter=self.write,          channels=(None, max_alias))
        self.add_command('USB:REAd',    getter=self.read,           channels=(None, max_alias))
        self.add_command('USB:ASK',     getter=self.query,          channels=(None, max_alias))

    def assign_alias(self, value, channels):
        if self.debugging: print("prior to reassignment: ", self.aliases)
        original_alias =int(channels[1])
        new_alias = int(value) 
        
        if new_alias == original_alias:
            return

        if original_alias in self.aliases:
            if self.debugging: print(f"Attempting to assign {new_alias} to {self.aliases[original_alias]} (previously {original_alias})")

            # Check if the new alias is already assigned to something
            if new_alias in self.aliases:
                # Swap the aliases: original_alias becomes new_alias and vice versa
                temp_device = self.aliases[original_alias]
                self.aliases[original_alias] = self.aliases[new_alias]
                self.aliases[new_alias] = temp_device

                if self.debugging:
                    print(f"Aliases {original_alias} and {new_alias} swapped.")
            else:
                # Reassign the alias to the new one if no conflict
                self.aliases[new_alias] = self.aliases[original_alias]
                del self.aliases[original_alias]  # Remove the old alias
                if self.debugging:
                    print(f"Alias {original_alias} reassigned to {new_alias}")
            
            # Optionally, fix missing aliases after reassignment
            self._fix_missing_aliases()
        else:
            raise Exception(f"Original alias {original_alias} is not assigned.")
        
        return

    
    def _fix_missing_aliases(self):
        # check that there are no missing devices. If there are, assign them to successively higher alias numbers.
        orphaned_devices = list(self.ports.keys())
        max_alias = 0

        for k, v in self.aliases.items():
            max_alias = max(k, max_alias)
            if v in orphaned_devices: orphaned_devices.remove(v)
        
        while orphaned_devices:
            max_alias += 1
            self.aliases[max_alias] = orphaned_devices.pop()


    def debug_print(self, func_name, value):
        if self.debugging:
            print(f"{func_name}: {value}")
    
    def list_devices(self):
        device_str = "list_devices_running: "
        for k, v in self.ports.items():
            # Find all aliases associated with the port
            current_aliases = list(filter(lambda name: self.aliases[name] == k, self.aliases))
            device_str += f"{current_aliases}({v[1]})"
        
        self.debug_print('list_devices', device_str)  # Debugging print before return
        return device_str

    def write(self, value, channels):
        device = self._lookup_device(channels[1])
        result = self._write(device, value)
        self.debug_print(f'writing {value} to {device}', result)
        self.debug_print('write', result)  # Debugging print before return
        return result
    
    def read(self, channels):
        device = self._lookup_device(channels[1])
        result = self._read(device)
        self.debug_print('read', result)  # Debugging print before return
        return result

    def _write(self, device, msg):
        # assumes msg is already in the form of a string
        ser = self.ports[device][0]
        self.debug_print(f"_write flushing {ser}", None)
        ser.flush()
        ser.write(msg.encode())
        self.debug_print(f'_write: {device} sent', msg)  # Debugging print before return
        return None
    
    def _lookup_device(self, alias):
        return self.aliases[alias]
    
    def _read(self, device):
        ser = self.ports[device][0]
        #read in lines from the input buffer 
        msg = '' 
        msg += ser.readline().decode('utf-8').rstrip()
       
        while ser.in_waiting:
            msg += ' ' + ser.readline().decode('utf_8').rstrip()
        if self.debugging:
            print(msg)

        self.debug_print('_read', msg)  # Debugging print before return
        return msg  # Return the joined decoded lines as a string
    
    def query(self, value, channels):
        device = self._lookup_device(channels[1])
        result = self._query(device, value)
        self.debug_print('query', result)  # Debugging print before return
        return result
    
    def _query(self, device, str_command):
        self._write(device, str_command)
        result = self._read(device)
        self.debug_print('_query', result)  # Debugging print before return
        return result

    def get_CPU_serial(self):
        serial = '?'
        try:
            cpuinfo = dict_from_strings(open('/proc/cpuinfo').readlines())
            serial = cpuinfo['Serial']
        finally:
            self.debug_print('get_CPU_serial', serial)  # Debugging print before return
            return serial
    
    def get_identification(self):
        ''' *IDN? mandatory command ''' 
        identification = 'SQDLab, Raspberry Pi USB, %s, V%d' % (self.get_CPU_serial(), self._REVISION)
        self.debug_print('get_identification', identification)  # Debugging print before return
        return identification
    
    def __del__(self):
        # iterate through all usb devices and close the serial connection
        for tuple in self.ports.values():
            tuple[0].close()

if __name__ == "__main__":
    pi = PiUSB(timeout=0.5, debugging=True)
    print(pi.list_devices())
