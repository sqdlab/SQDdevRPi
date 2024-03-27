#Original author: Markus Jerger
#Created approximately: 29/09/2014
#Modified by Prasanna Pakkiam to make it compatible with Python3 and the new Raspberry Pi OS

import time

from scpi_base import SCPIBase
from scpi_event import SCPIDeviceError, SCPIQueryError
import RPi.GPIO as GPIO

def dict_from_strings(strings):
    ''' take a list of key:value pairs and return them as a dictionary '''
    return dict([s.strip() for s in kv.split(':', 1)] for kv in strings if ':' in kv)

class PiGPIO(SCPIBase):    
    _REVISION = 1
    
    class Pin:
        def __init__(self, gpio, mode_rst, val_rst, pud_rst, setup = True, mode_fix = False, val_fix = False, pud_fix = False, description = None):
            '''
                pin description

                Input:
                    mode_rst, val_rst, pud_rst -- mode, value, pull up/down state at reset
                    setup (bool) - indicates if the pin can be setup. False implies mode_fix, val_fix and pud_fix
                    mode_fix, val_fix, pud_fix (bool) -- indicates that mode/val/pud can not be changed
                    description - user-friendly pin information
            '''
            self.id = gpio
            self.mode_rst = mode_rst
            self.val_rst = val_rst
            self.pud_rst = pud_rst
            self.setup = setup
            if not setup:
                self.mode_fix = True
                self.val_fix = True
                self.pud_fix = True
            else:
                self.mode_fix = mode_fix
                self.val_fix = val_fix
                self.pud_fix = pud_fix
            self.description = description
            self.reset()
        
        def _setup(self):
            if self.setup:
                if self.mode == GPIO.OUT:
                    GPIO.setup(self.id, self.mode) #, pull_up_down=self.pud, initial=self.val)  <--- Causes issues with Pin3/GPIO2 - check later why?!
                else:  
                    GPIO.setup(self.id, self.mode, pull_up_down=self.pud)
                
        def reset(self):
            self.mode = self.mode_rst
            self.pud = self.pud_rst
            self.val = self.val_rst
            self._setup()
            
        def set_mode(self, mode):
            if self.mode_fix:
                if self.mode != mode:
                    raise ValueError('mode of pin %d is fixed.'%self.id)
            else:
                self.mode = mode
                self._setup()
        
        def set_pud(self, pud):
            if self.pud_fix:
                if self.pud != pud:
                    raise ValueError('pull-up/down resistor of pin %d is fixed.'%self.id)
            else:
                self.pud = pud
                self._setup()

        def set_val(self, val):
            #if self.mode != GPIO.OUT:
            #    raise ValueError('unable to set value of input pin %d.'%self.id)
            if self.val_fix:
                if self.val != val:
                    raise ValueError('value of pin %d is fixed.'%self.id)
            else:
                self.val = val
                if self.mode == GPIO.OUT:
                    GPIO.output(self.id, val)
                
        def get_val(self):
            ''' read pin value from hardware. value is not stored in self.val '''
            if self.val_fix:
                return self.val_rst
            else:
                return GPIO.input(self.id)
            
    def __init__(self):
        super(PiGPIO, self).__init__()
        # set pin numbering to 'board', reset all pins to their default values
        GPIO.setmode(GPIO.BOARD)
        self._pins = [
            None, # pin counting starts from 1
            PiGPIO.Pin(1, GPIO.OUT, True, GPIO.PUD_UP, setup=False, mode_fix=True, val_fix=True, pud_fix=True, description='3V3 supply'),
            PiGPIO.Pin(2, GPIO.OUT, True, GPIO.PUD_UP, setup=False, mode_fix=True, val_fix=True, pud_fix=True, description='5V supply'),
            PiGPIO.Pin(3, GPIO.OUT, False, GPIO.PUD_UP, pud_fix=True, description='I2C_SDA'),
            PiGPIO.Pin(4, GPIO.OUT, True, GPIO.PUD_UP, setup=False, mode_fix=True, val_fix=True, pud_fix=True, description='5V supply'),
            PiGPIO.Pin(5, GPIO.OUT, False, GPIO.PUD_UP, pud_fix=True, description='I2C_SCL'),
            PiGPIO.Pin(6, GPIO.OUT, False, GPIO.PUD_DOWN, setup=False, mode_fix=True, val_fix=True, pud_fix=True, description='GND'),
            PiGPIO.Pin(7, GPIO.OUT, False, GPIO.PUD_OFF, description='GPIO'),
            PiGPIO.Pin(8, GPIO.OUT, False, GPIO.PUD_OFF, description='GPIO'),
            PiGPIO.Pin(9, GPIO.OUT, False, GPIO.PUD_DOWN, setup=False, mode_fix=True, val_fix=True, pud_fix=True, description='GND'),
            PiGPIO.Pin(10, GPIO.OUT, False, GPIO.PUD_OFF, description='GPIO'),
            PiGPIO.Pin(11, GPIO.OUT, False, GPIO.PUD_OFF, description='GPIO'),
            PiGPIO.Pin(12, GPIO.OUT, False, GPIO.PUD_OFF, description='GPIO'),
            PiGPIO.Pin(13, GPIO.OUT, False, GPIO.PUD_OFF, description='GPIO'),
            PiGPIO.Pin(14, GPIO.OUT, False, GPIO.PUD_DOWN, setup=False, mode_fix=True, val_fix=True, pud_fix=True, description='GND'),
            PiGPIO.Pin(15, GPIO.OUT, False, GPIO.PUD_OFF, description='GPIO'),
            PiGPIO.Pin(16, GPIO.OUT, False, GPIO.PUD_OFF, description='GPIO'),
            PiGPIO.Pin(17, GPIO.OUT, True, GPIO.PUD_UP, setup=False, mode_fix=True, val_fix=True, pud_fix=True, description='3V3 supply'),
            PiGPIO.Pin(18, GPIO.OUT, False, GPIO.PUD_OFF, description='GPIO'),
            PiGPIO.Pin(19, GPIO.OUT, False, GPIO.PUD_OFF, description='GPIO'),
            PiGPIO.Pin(20, GPIO.OUT, False, GPIO.PUD_DOWN, setup=False, mode_fix=True, val_fix=True, pud_fix=True, description='GND'),
            PiGPIO.Pin(21, GPIO.OUT, False, GPIO.PUD_OFF, description='GPIO'),
            PiGPIO.Pin(22, GPIO.OUT, False, GPIO.PUD_OFF, description='GPIO'),
            PiGPIO.Pin(23, GPIO.OUT, False, GPIO.PUD_OFF, description='GPIO'),
            PiGPIO.Pin(24, GPIO.OUT, False, GPIO.PUD_OFF, description='GPIO'),
            PiGPIO.Pin(25, GPIO.OUT, False, GPIO.PUD_DOWN, setup=False, mode_fix=True, val_fix=True, pud_fix=True, description='GND'),
            PiGPIO.Pin(26, GPIO.OUT, False, GPIO.PUD_OFF, description='GPIO'),
            None,
            None,
            PiGPIO.Pin(29, GPIO.OUT, False, GPIO.PUD_OFF, description='GPIO'),
            PiGPIO.Pin(30, GPIO.OUT, False, GPIO.PUD_DOWN, setup=False, mode_fix=True, val_fix=True, pud_fix=True, description='GND'),
            PiGPIO.Pin(31, GPIO.OUT, False, GPIO.PUD_OFF, description='GPIO'),
            PiGPIO.Pin(32, GPIO.OUT, False, GPIO.PUD_OFF, description='GPIO'),
            PiGPIO.Pin(32, GPIO.OUT, False, GPIO.PUD_OFF, description='GPIO'),
            PiGPIO.Pin(33, GPIO.OUT, False, GPIO.PUD_OFF, description='GPIO'),
            PiGPIO.Pin(34, GPIO.OUT, False, GPIO.PUD_DOWN, setup=False, mode_fix=True, val_fix=True, pud_fix=True, description='GND'),
            PiGPIO.Pin(35, GPIO.OUT, False, GPIO.PUD_OFF, description='GPIO'),
            PiGPIO.Pin(36, GPIO.OUT, False, GPIO.PUD_OFF, description='GPIO'),
            PiGPIO.Pin(37, GPIO.OUT, False, GPIO.PUD_OFF, description='GPIO'),
            PiGPIO.Pin(38, GPIO.OUT, False, GPIO.PUD_OFF, description='GPIO'),
            PiGPIO.Pin(39, GPIO.OUT, False, GPIO.PUD_DOWN, setup=False, mode_fix=True, val_fix=True, pud_fix=True, description='GND'),
            PiGPIO.Pin(40, GPIO.OUT, False, GPIO.PUD_OFF, description='GPIO')
        ]
        # add commands to the SCPI parser
        nch = 40
        self.add_command('GPIO:MEASure:DIGital:DATA', getter=self.read_pin_value, channels=(None,None,None,nch))
        self.add_command('GPIO:MEASure:DIGital:PULL', getter=self.get_pin_pullupdown, setter=self.set_pin_pullupdown, channels=(None,None,None,nch))
        self.add_command('GPIO:SOURce:DIGital:DATA', getter=self.get_pin_value, setter=self.set_pin_value, channels=(None,None,None,nch))
        self.add_command('GPIO:SOURce:DIGital:IO', getter=self.get_pin_direction, setter=self.set_pin_direction, channels=(None,None,None,nch))
        self.add_command('GPIO:SOURce:DIGital:PULSe', setter=self.pulse_pin_value, channels=(None,None,None,nch))

    def _check_arg(self, info, value, options):
        if isinstance(value, str):
            value = value.upper()
        if value not in options:
            raise SCPIQueryError(info='%s must be one of [%s].'%(info, ', '.join([str(o) for o in options])))
        if isinstance(options, dict):
            return options[value]

    def set_pin_pullupdown(self, value, channels):
        '''
            control pull-up and pull-down resistors of a pin
        '''
        pin = self._pins[channels[-1]]
        pud_map = {'UP': GPIO.PUD_UP, 'DOWN': GPIO.PUD_DOWN, 'NONE': GPIO.PUD_OFF}
        pud = self._check_arg('PULL', value, pud_map)
        try:
            pin.set_pud(pud)
        except ValueError as err:
            raise SCPIDeviceError(info = err)
        
    def get_pin_pullupdown(self, channels):
        '''
            retrieve setting of the pull-up and pull-down resistors of a pin
        '''
        pin = self._pins[channels[-1]]
        pud_map = {GPIO.PUD_UP: 'UP', GPIO.PUD_DOWN: 'DOWN', GPIO.PUD_OFF: 'NONE'}
        return pud_map[pin.pud]

    def set_pin_direction(self, value, channels):
        '''
            switch pin between input and output
        '''
        pin = self._pins[channels[-1]]
        mode_map = {'IN': GPIO.IN, 'OUT': GPIO.OUT}
        mode = self._check_arg('direction', value, mode_map)
        try:
            pin.set_mode(mode)
        except ValueError as err:
            raise SCPIDeviceError(info = err)

    def get_pin_direction(self, channels):
        '''
            return direction setting of a pin
        '''
        pin = self._pins[channels[-1]]
        mode_map = {GPIO.IN: 'IN', GPIO.OUT: 'OUT', GPIO.I2C: 'I2C', GPIO.PWM: 'PWM', GPIO.SERIAL: 'SERIAL'}
        return mode_map[pin.mode]

    def read_pin_value(self, channels):
        '''
            read pin state
        '''
        pin = self._pins[channels[-1]]
        return pin.get_val() 
        
    
    def get_pin_value(self, channels):
        '''
            return last set pin state
        '''
        pin = self._pins[channels[-1]]
        return pin.val 
    
    def set_pin_value(self, value, channels):
        '''
            write pin state
        '''
        pin = self._pins[channels[-1]]
        value_map = {'0': False, '1': True, 'LOW': False, 'HIGH': True, 'FALSE': False, 'TRUE': True}
        value = self._check_arg('DATA', value, value_map)
        try:
            pin.set_val(value)
        except ValueError as err:
            raise SCPIDeviceError(info = err)

    def pulse_pin_value(self, value, delay, channels):
        '''
            pulse pin from current value to target value and return to current value after a set delay
        '''
        pin = self._pins[channels[-1]]
        value_map = {'0': False, '1': True, 'LOW': False, 'HIGH': True, 'FALSE': False, 'TRUE': True}
        value = self._check_arg('DATA', value, value_map)
        DELAY_CORRECTION = -190e-6
        try:
            delay = float(delay)
            if(delay<200e-6) or (delay>2.):
                raise SCPIQueryError(info='delay must be between 200us and 2s.')
        except ValueError:
            raise SCPIQueryError(info='unable to convert "%s" to float.'%delay)
        try:
            cur = pin.val
            pin.set_val(value)
            time.sleep(delay+DELAY_CORRECTION)
            pin.set_val(cur)
        except ValueError as err:
            raise SCPIDeviceError(info = err)
        

    def get_serial(self):
        serial = '?'
        try:
            cpuinfo = dict_from_strings(open('/proc/cpuinfo').readlines())
            serial = cpuinfo['Serial']
        finally:
            return serial
    
    def get_identification(self):
        ''' *IDN? mandatory command ''' 
        return 'SQDLab, Raspberry Pi GPIO, %s, V%d'%(self.get_serial(), self._REVISION)
    
    def reset(self):
        '''
            reset the instrument
            
            set all pins to input (high impedance), so no power is sourced or sunk
        '''
        pass
    
    
if __name__ == '__main__':
    pi = PiGPIO()
    while True:
        user = raw_input()
        device = pi.process(user)
        print( '\n'.join(device) + '\n')
    #print pi.process('*IDN?')
    #if len(pi.errors): print pi.errors.popleft()
    #pass