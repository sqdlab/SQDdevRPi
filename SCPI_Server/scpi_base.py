#Original author: Markus Jerger
#Created approximately: 29/09/2014
#Modified by Prasanna Pakkiam to make it compatible with Python3 and the new Raspberry Pi OS

import collections
import re
import math

from scpi_event import SCPINoError, SCPIError, SCPIEvent
import scpi_event as se

def block_pack(data):
    ''' generate a definite length arbitrary block response from data '''
    return '#%d%d%s'%(len(str(len(data))), len(data), data)

class SCPIBase(object):
    '''
        
    '''
    # status byte flags
    STB_USER0 = 1<<0
    STB_USER1 = 1<<1
    STB_ERROR = 1<<2
    STB_QUESTIONABLE = 1<<3
    STB_MESSAGE_AVAILABLE = 1<<4
    STB_SESR = 1<<5
    STB_SERVICE_REQUEST = 1<<6
    STB_OPERATION = 1<<7
    # _standard_event_status register flags
    SESR_OPERATION_COMPLETE = 1<<0
    SESR_REQUEST_CONTROL = 1<<1
    SESR_QUERY_ERROR = 1<<2
    SESR_DEVICE_DEPENDENT_ERROR = 1<<3
    SESR_EXECUTION_ERROR = 1<<4
    SESR_COMMAND_ERROR = 1<<5
    SESR_USER_REQUEST = 1<<6
    SESR_POWER_ON = 1<<7
    # _operation_status register flags
    OPER_CALIBRATING = 1<<0
    OPER_SETTLING = 1<<1
    OPER_RANGING = 1<<2
    OPER_SWEEPING = 1<<3
    OPER_MEASURING = 1<<4
    OPER_WAIT_TRIGGER = 1<<5
    OPER_WAIT_ARM = 1<<6
    OPER_CORRECTING = 1<<7
    OPER_USER0 = 1<<8
    OPER_USER1 = 1<<9
    OPER_USER2 = 1<<10
    OPER_USER3 = 1<<11
    OPER_USER4 = 1<<12
    OPER_INSTRUMENT_SUMMARY = 1<<13
    OPER_PROGRAM_RUNNING = 1<<14
    # _questionable_status register flags
    QUES_VOLTAGE = 1<<0
    QUES_CURRENT = 1<<1
    QUES_TIME = 1<<2
    QUES_POWER = 1<<3
    QUES_TEMPERATURE = 1<<4
    QUES_FREQUENCY = 1<<5
    QUES_PHASE = 1<<6
    QUES_MODULATION = 1<<7
    QUES_CALIBRATION = 1<<8
    QUES_USER0  = 1<<9
    QUES_USER1  = 1<<10
    QUES_USER2  = 1<<11
    QUES_USER3  = 1<<12
    QUES_INSTRUMENT_SUMMARY = 1<<13
    QUES_COMMAND_WARNING = 1<<14

    class Command:
        def __init__(self, name, getter, setter, channels, re):
            self.name = name
            self.get = getter
            self.set = setter
            self.channels = channels
            self.re = re
    
    def __init__(self):
        '''
            initialize SCPI parser
        '''
        # add mandatory gpib commands
        if not hasattr(self, '_commands'):
            self._commands = {}
        self.add_command('*CLS', self.status_clear)
        self.add_command('*ESE', self.set_standard_event_status_enable, self.get_standard_event_status_enable)
        self.add_command('*ESR', getter=self.get_standard_event_status)
        self.add_command('*IDN', getter=self.get_identification)
        self.add_command('*OPC', self.set_operation_complete, self.get_operation_complete)
        self.add_command('*RST', self.reset)
        self.add_command('*SRE', self.set_service_request_enable, self.get_service_request_enable)
        self.add_command('*STB', getter=self.get_status_byte)
        self.add_command('*TST', getter=self.get_self_test)
        self.add_command('*WAI', self.wait)
        # add mandatory scpi commands
        self.add_command('SYSTem:ERRor', getter=self.get_error)
        self.add_command('SYSTem:ERRor:NEXT', getter=self.get_error) # same as SYST:ERR
        self.add_command('SYSTem:VERSion', getter=self.get_version)
        self.add_command('STATus:OPERation', getter=self.get_operation_event)
        self.add_command('STATus:OPERation:EVENT', getter=self.get_operation_event) # same as STAT:OPER
        self.add_command('STATus:OPERation:CONDition', getter=self.get_operation_condition)
        self.add_command('STATus:OPERation:ENABle', self.set_operation_enable, self.get_operation_enable)
        self.add_command('QUEStionable', getter=self.get_questionable_event)
        self.add_command('QUEStionable:EVENt', getter=self.get_questionable_event) # same as QUES
        self.add_command('QUEStionable:CONDition', getter=self.get_questionable_condition)
        self.add_command('QUEStionable:ENABle', self.set_questionable_enable, self.get_questionable_enable)
        self.add_command('PRESet', self.preset)
        # non-mandatory scpi commands
        self.add_command('SYSTem:HELP:HEADers', getter=self.get_headers)
        # reset status registers
        self.status_clear()
        self._standard_event_status_mask = 0
        self._status_byte_summary_mask = 0
        self._questionable_summary_mask = 0
        self._operation_summary_mask = 0
        
    
    def add_command(self, name, setter = None, getter = None, channels = None):
        '''
            add a new command to the parser
            
            Input:
                name (string): 
                    command name and aliases, separated by semicolons 
                setter (function):
                    function called when command is received in command form 
                getter (function):
                    function called when command is received in query form
                channels (list of int):
                    number of channels at each hierarchy level. the execute unit passes 
                    the channel number(s) provided by the client to the getter and setter 
                    functions as a list via a channels keyword argument.
                    If channels is None, no such argument is passed and an Exception is
                    raised if the user specifies a channel number.
        '''
        # call parser to check the command for validity
        for name_parts, _, _, _ in self.parse(name):
            # ignore channels numbers and arguments if provided in name
            name = ':'.join(name_parts)
            # check number of channels
            if (channels is not None):
                channel_count_diff = len(name_parts) - len(channels)
                if channel_count_diff < 0:
                    raise ValueError('number of entries of channels is larger than the hierarchy level.')
                elif channel_count_diff > 0:
                    channels.extend([None]*channel_count_diff)

            # generate and compile regular expression matching command
            regex_parts = []
            name_part_dicts = []
            for name_part in name_parts:
                name_part_dict = re.match(r'\A(?P<long>(?P<short>\*?[A-Z]+)[a-z]*)\Z', name_part).groupdict()
                if not name_part_dict['short']:
                    raise ValueError('empty short form provided for %s.'%name_part)
                name_part_dicts.append(name_part_dict)
                name_part_dict = dict((key, re.escape(value)) for key, value in name_part_dict.items())
                regex_parts.append('(%(short)s|%(long)s)'%name_part_dict)
            regex = re.compile(r'\A%s\Z'%(':'.join(regex_parts)), flags = re.IGNORECASE) 
            # check if the command is already in the command list
            for variant_idx in range(1<<len(name_part_dicts)):
                name_part_indices = [('long' if variant_idx&(1<<bit) else 'short') for bit in range(len(name_part_dicts))]
                name_variant = ':'.join([d[i] for d, i in zip(name_part_dicts, name_part_indices)])
                command_conflicting = self.find(name_variant) 
                if command_conflicting is not None:
                    raise ValueError('command %s conflicts with previously defined command %s'%(name, command_conflicting.name))
            # create command list entry
            self._commands[name] = SCPIBase.Command(name = name, getter = getter, setter = setter, channels = channels, re = regex)
    
    def process(self, text):
        '''
            parse and execute client input, return command output
        '''
        outputs = []
        try:
            tokens = self.parse(text)
            for token in tokens:
                output = self.execute(*token)
                if output is not None:
                    output = self.format_output(output)
                    outputs.append(output)
        except SCPIEvent as err:
            self.errors.append(err)
        #except Exception as err:
        #    self.errors.append(se.SCPIExecutionError(info = str(err)))
        return outputs
    
    def format_output(self, output):
        '''
            convert output to string
            (no frills here)
        '''
        if isinstance(output, bool):
            return '1' if output else '0'
        elif isinstance(output, int):
            return str(output)
        else:
            return str(output)
    
    def error(self, error):
        '''
            add a new error object to the error queue,
            setting event flags where appropriate
        '''
        # TODO
        pass
    
    def parse(self, text):
        '''
            parse SCPI input provided by the client
            
            the command structure is hierarchical.
            when a new input is parsed, the parser starts in the top hierarchy level
            a mnemonic followed by a colon moves down one level
            a colon at the start of a command moves up one level.
            the current level is retained between multiple commands appearing on the same
                line. a semicolon separates multiple commands on the same line.
            
            digits can be appended to mnemonics to indicate channel numbers.
            strings are delimited by double quotes
            
            Input:
                text(string) - command line received from the client
            Output:
                list of (list, bool, list) - 
                    the first list in each tuple contains the fully qualified path to the command, 
                    the boolean value indicates that the command is a query, 
                    the second list contains the arguments
        '''
        # take input apart at semicolons, 
        # disregarding semicolons enclosed in double quotes
        # stripping white-space
        cmds = re.findall(r' *((?:(?:"[^"]*")|[^";])*);? *', text)
        cmd_base = []
        tokens = []
        for cmd in cmds:
            # ignore empty commands
            if not len(cmd):
                continue
            # split command from argument list
            if ' ' in cmd:
                cmd, arg_str = [s.strip() for s in cmd.split(' ', 1)]
                # also split argument list
                args = re.findall(r'( *"[^"]*"|[^",]+)(?:,|\Z)', arg_str)
                # make sure every letter is accounted for
                if sum(len(arg) for arg in args)+len(args)-1 != len(arg_str):
                    raise SCPIEvent.factory(se.CODE_SYNTAX_ERROR, info = 'in argument list')
                # strip white-space and quotes (there are exactly zero or two quotes in each arg)
                args = [arg.strip('" ') for arg in args]
            else:
                args = []
            # determine if the command is a set or get operation
            if cmd[-1] == '?':
                query = True
                # remove trailing ?
                cmd = cmd[:-1]
            else:
                query = False
            cmd_parts = cmd.split(':')
            # command tree traversal, build full command path
            cmd_parts = cmd_base + cmd_parts
            idx = 0
            while idx < len(cmd_parts):
                if(cmd_parts[idx] == ''):
                    if(not idx):
                        raise SCPIEvent.factory(se.CODE_SYNTAX_ERROR, info = 'command refers to a level above the root of the command tree')
                    del cmd_parts[idx]
                    del cmd_parts[idx-1]
                    idx -= 1
                else:
                    idx += 1
            cmd_base = cmd_parts[:-1]
            # extract channel numbers and check format
            mnemonics = []
            channels = []
            for cmd_part_index, cmd_part in enumerate(cmd_parts):
                # all parts must be alphabetic with an optional numeric suffix
                if cmd_part_index:
                    m = re.match('\A([A-Za-z]+)([0-9]*)\Z', cmd_part)
                else:
                    m = re.match('\A(\*?[A-Za-z]+)([0-9]*)\Z', cmd_part)
                if m is None:
                    raise SCPIEvent.factory(se.CODE_SYNTAX_ERROR, info = 'in command name')
                mnemonic, channel = m.groups()
                mnemonics.append(mnemonic)
                channels.append(int(channel) if (channel != '') else None)
            # execute command (no longer)
            tokens.append((mnemonics, channels, query, args))
        return tokens
    
    def find(self, name):
        '''
            look up name in the command list and return the corresponding command list entry
        '''
        for command in self._commands.values():
            if command.re.match(name) is not None:
                return command
        return None
        
        
    def execute(self, name, channels, query, args):
        '''
            look a command up in the command list, execute it and handle 
        
            Input:
                name (list of string) - path to command
                channels (list of int) - channel chosen at every hierarchy level
                query (bool) - indicates a query
                args (list of string) - argument list to command  
        '''
        # find matching command
        name = ':'.join(name)
        command = self.find(name)
        if command is None:
            raise SCPIEvent.factory(se.CODE_SYNTAX_ERROR, info = 'unsupported command %s.'%name)
        kwargs = {}
        # check and mangle channel numbers
        if command.channels is not None:
            for idx in range(len(command.channels)):
                if (channels[idx] is not None):
                    # check if provided channel numbers are expected and in range
                    if(command.channels is None) or (command.channels[idx] is None):
                        raise SCPIEvent.factory(se.CODE_SYNTAX_ERROR, info = 'channel index unexpected at index %d'%idx)
                    if (channels[idx] < 1) or (channels[idx] > command.channels[idx]):
                        raise SCPIEvent.factory(se.CODE_SYNTAX_ERROR, info = 'channel index %d at index %d out of range'%(channels[idx], idx))
                else:
                    # if a channel number is expected but not provided use channel 1
                    if(command.channels[idx] is not None):
                        channels[idx] = 1
            kwargs['channels'] = channels
        # execute function
        func = command.get if query else command.set
        if func is None:
            raise SCPIEvent.factory(se.CODE_SYNTAX_ERROR, info = '%s not allowed.'%('GET' if query else 'SET'))
        try:
            result = func(*args, **kwargs)
        except TypeError as e:
            raise SCPIEvent.factory(se.CODE_SYNTAX_ERROR, info = str(e))
        if query:
            return result
    
    #
    # suite of mandatory GPIB commands
    # 
    def status_clear(self):
        ''' 
            clear status command.
            
            expected to clear SESR, OPER status, QUES status and error/event queue 
        '''
        self._service_request = False
        self.standard_event_status_clear()
        self.questionable_clear()
        self.operation_clear()
        self.error_clear()

    def standard_event_status_clear(self):
        ''' clear standard event status register '''
        self._standard_event_status = 0
    
    def set_standard_event_status_enable(self, mask):
        ''' standard event status enable command. '''
        mask = int(mask)
        if (mask < 0) or (mask >= 2**7):
            raise ValueError('enable mask must be between 0 and 2**7-1.')
        self._standard_event_status_mask = mask
    
    def get_standard_event_status_enable(self):
        ''' standard event status enable query. '''
        return self._standard_event_status_mask

    def get_standard_event_status(self):
        ''' standard event status register query, destructive '''
        status = self._standard_event_status
        self.standard_event_status_clear()
        return status
    
    def set_operation_complete(self):
        ''' 
            operation complete command
            
            assumes the device does not support overlapping commands
            sets the OPERATION_COMPLETE flag of the standard event status register immediately 
        '''
        self._standard_event_status |= self.SESR_OPERATION_COMPLETE
    
    def get_operation_complete(self):
        ''' 
            operation complete query
            
            assumes the device does not support overlapping commands
            returns True immediately 
        '''
        return '1'

    def wait(self):
        ''' wait-to-continue command '''
        pass
   
    def get_identification(self):
        ''' identification query '''
        return 'SQDLab, SCPIBase, ?, ?'

    def reset(self):
        ''' 
            reset command
            
            reset should leave the device in a well-defined state suitable
            for remote control. source instruments should not output any
            current or voltage.
            status structures are not affected by reset. 
        '''
        pass
    
    def set_service_request_enable(self, mask):
        ''' define the mask defining which bits of the status byte are reported in the summary bit '''
        mask = int(mask)
        if (mask < 0) or (mask >= 2**7):
            raise ValueError('enable mask must be between 0 and 2**7-1.')
        self._status_byte_summary_mask = mask
    
    def get_service_request_enable(self):
        ''' return status byte summary mask '''
        return self._status_byte_summary_mask

    def get_status_byte(self):
        ''' status byte query '''
        status = 0
        # USER0, USER1
        if len(self.errors):
            status |= self.STB_ERROR
        if self.get_questionable_condition() & self.QUES_INSTRUMENT_SUMMARY:
            status |= self.STB_QUESTIONABLE
        # MESSAGE_AVAILABLE
        if self.get_standard_event_status() & self._standard_event_status_mask:
            status |= self.STB_SESR
        if self.get_operation_condition() & self.OPER_INSTRUMENT_SUMMARY:
            status |= self.STB_OPERATION
        if status & self._status_byte_summary_mask:
            status |= self.STB_SERVICE_REQUEST
        return status
    
    def get_self_test(self):
        ''' self-test query '''
        return '0'
    
    #
    # suite of standard SCPI commands
    #
    def error_clear(self):
        ''' clear error queue '''
        if hasattr(self, 'errors'):
            self.errors.clear()
        else:
            self.errors = collections.deque()
    
    def get_error(self):
        ''' return next error in the error queue '''
        try:
            error = self.errors.popleft()
        except:
            error = SCPINoError()
        finally:
            return str(error)
    
    def operation_clear(self):
        ''' clear operation status register '''
        self._operation_status = 0
    
    def get_operation_event(self):
        ''' return operation condition event register, clearing it '''
        status = self.get_operation_condition()
        self.operation_clear()
        return status
    
    def get_operation_condition(self):
        ''' return operation condition register non-destructively '''
        status = self._operation_status
        # generate summary bit
        if self._operation_status & self._operation_summary_mask:
            status |= self.OPER_INSTRUMENT_SUMMARY
        return status
    
    def set_operation_enable(self, mask):
        ''' define the mask defining which bits of questionable are reported in the summary bit '''
        mask = int(mask)
        if (mask < 0) or (mask >= 2**15):
            raise ValueError('enable mask must be between 0 and 2**15-1.')
        self._operation_summary_mask = mask
    
    def get_operation_enable(self):
        ''' return questionable summary reporting mask '''
        return self._operation_summary_mask

    def questionable_clear(self):
        ''' clear operation status register '''
        self._questionable_status = 0

    def get_questionable_event(self):
        ''' return questionable event register, clearing it '''
        status = self.get_questionable_condition()
        self.questionable_clear()
        return status

    def get_questionable_condition(self):
        ''' return questionable condition register non-destructively '''
        status = self._questionable_status
        # generate summary bit
        if status & self._questionable_summary_mask:
            status |= self.QUES_INSTRUMENT_SUMMARY
        return status 
        
    def set_questionable_enable(self, mask):
        ''' define the mask defining which bits of questionable are reported in the summary bit '''
        mask = int(mask)
        if (mask < 0) or (mask >= 2**15):
            raise ValueError('enable mask must be between 0 and 2**15-1.')
        self._questionable_summary_mask = mask
    
    def get_questionable_enable(self):
        ''' return questionable summary reporting mask '''
        return self._questionable_summary_mask
          
    def preset(self):
        ''' 
            preset command
            
            preset should leave the device in a well-defined state suitable
            for interactive (local) control
        '''
        return self._reset() 
    
    def get_version(self):
        ''' return SCPI version the device complies to '''
        return '1999.0'
    
    
    #
    # useful non-mandatory commands
    #
    def get_headers(self):
        '''
            return all supported commands
        '''
        names = []
        for name, command in self._commands.items():
            for name_parts, _, _, _ in self.parse(name):
                # add numeric suffix indication
                # {digits}, {number,number,...}, {start:stop}, {?:?}
                if command.channels is not None:
                    for name_part_idx in range(len(name_parts)):
                        if command.channels[name_part_idx]:
                            name_parts[name_part_idx] += '{1:%d}'%command.channels[name_part_idx]
                
                name = ':'.join(name_parts)
                # append no query/query only etc. suffixes
                if command.get is None:
                    if command.set is None:
                        name += '/unknown/'
                    else:
                        name += '/nquery'
                else:
                    if command.set is None:
                        name += '?/qonly'
                    else:
                        pass
                names.append(name)
        return block_pack('\n'.join(sorted(names)))
        pass
        
