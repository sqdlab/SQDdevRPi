#Original author: Markus Jerger
#Created approximately: 29/09/2014
#Modified by Prasanna Pakkiam to make it compatible with Python3 and the new Raspberry Pi OS

CODE_NO_ERROR = 0
CODE_COMMAND_ERROR = -100
CODE_SYNTAX_ERROR = -102
CODE_DATA_TYPE_ERROR = -104
CODE_GET_NOT_ALLOWED = -105
CODE_PARAMETER_NOT_ALLOWED = -108
CODE_MISSING_PARAMETER = -109
# a lot more codes here
CODE_EXECUTION_ERROR = -200
CODE_PARAMETER_ERROR = -220
# a lot more codes here
CODE_DEVICE_ERROR = -300
# a lot more codes here
CODE_QUERY_ERROR = -400
CODE_QUERY_INTERRUPTED = -410
CODE_QUERY_UNTERMINATED = -420
CODE_QUERY_DEADLOCKED = -430
CODE_QUERY_UNTERMINATED_INDEFINITE = -440
CODE_POWER_ON_EVENT = -500
CODE_USER_REQUEST_EVENT = -600
CODE_REQUEST_CONTROL_EVENT = -700
CODE_OPERATION_COMPLETE_EVENT = -800


MESSAGES = {
    CODE_NO_ERROR: 'No error',
    CODE_COMMAND_ERROR: 'Command error',
    CODE_EXECUTION_ERROR: 'Execution error',
    CODE_DEVICE_ERROR: 'Device-specific error',
    CODE_QUERY_ERROR: 'Query error',
    CODE_QUERY_INTERRUPTED: 'Query INTERRUPTED',
    CODE_QUERY_UNTERMINATED: 'Query UNTERMINATED',
    CODE_QUERY_DEADLOCKED: 'Query DEADLOCKED',
    CODE_QUERY_UNTERMINATED_INDEFINITE: 'Query UNTERMINATED after indefinite response',
    CODE_POWER_ON_EVENT: 'Power on',
    CODE_USER_REQUEST_EVENT: 'User request',
    CODE_REQUEST_CONTROL_EVENT: 'Request control',
    CODE_OPERATION_COMPLETE_EVENT: 'Operation complete'
}


class SCPIEvent(Exception):
    '''
        base class of SCPI events and errors
    '''
    def __init__(self, code, message = None, info = None):
        '''
            Input:
                code - event code between -2**15 and 2**15-1. 
                    negative numbers are reserved, zero indicates no error
                message - error description
                info - device-dependent additional information 
        '''
        if message is None:
            for message_code in (code, SCPIEvent.round_code(code, 10), SCPIEvent.round_code(code, 100)):
                if message_code in MESSAGES:
                    message = MESSAGES[message_code]
                    break
        if info is not None:
            message = '%s;%s'%(message, info)
        super(Exception, self).__init__(code, message)

    @staticmethod
    def factory(code, message = None, info = None):
        '''
            select correct return type depending on the event code provided
        '''
        classes = {
            CODE_NO_ERROR: SCPINoError,
            CODE_COMMAND_ERROR: SCPICommandError,
            CODE_EXECUTION_ERROR: SCPIExecutionError,
            CODE_DEVICE_ERROR: SCPIDeviceError,
            CODE_QUERY_ERROR: SCPIQueryError,
            CODE_POWER_ON_EVENT: SCPIPowerOnEvent,
            CODE_USER_REQUEST_EVENT: SCPIUserRequestEvent,
            CODE_REQUEST_CONTROL_EVENT: SCPIRequestControlEvent,
            CODE_OPERATION_COMPLETE_EVENT: SCPIOperationCompleteEvent
        }
        try:
            return classes[SCPIEvent.round_code(code, 100)](code, message, info)
        except:
            return SCPIEvent(code, message, info)

    @staticmethod
    def round_code(code, N):
        ''' round message code towards zero to a multiple of N '''
        code = int(code)
        if code < 0:
            return -N*int(-code/N)
        else:
            return N*int(code/N)
        
    def __str__(self):
        return '%d,"%s"'%self.args

class SCPINoError(SCPIEvent):
    '''
        no error
    '''
    def __init__(self, code = CODE_NO_ERROR, message = None, info = None):
        SCPIEvent.__init__(self, code, message, info)
    
class SCPIError(SCPIEvent):
    '''
        base class of SCPI errors
    '''
    pass

class SCPICommandError(SCPIError):
    '''
        An error in the execution block
        Bit 5 in SESR should be set on occurrence
    '''
    def __init__(self, code = CODE_COMMAND_ERROR, message = None, info = None):
        SCPIError.__init__(self, code, message, info)

class SCPIExecutionError(SCPIError):
    '''
        An error in the execution block
        Bit 4 in SESR should be set on occurrence
    '''
    def __init__(self, code = CODE_EXECUTION_ERROR, message = None, info = None):
        SCPIError.__init__(self, code, message, info)

class SCPIDeviceError(SCPIError):
    '''
        A device-specific error
        Bit 3 in SESR should be set on occurrence
    '''
    def __init__(self, code = CODE_DEVICE_ERROR, message = None, info = None):
        SCPIError.__init__(self, code, message, info)

class SCPIQueryError(SCPIError):
    '''
        A query error event.
        Bit 2 in SESR should be set on occurrence.
    '''
    def __init__(self, code = CODE_QUERY_ERROR, message = None, info = None):
        SCPIError.__init__(self, code, message, info)

class SCPIPowerOnEvent(SCPIEvent):
    '''
        A power on event
        Bit 7 in SESR should be set on occurrence.
    '''
    def __init__(self, code = CODE_POWER_ON_EVENT, message = None, info = None):
        SCPIEvent.__init__(self, code, message, info)

class SCPIUserRequestEvent(SCPIEvent):
    '''
        A user request event
        Bit 6 in SESR should be set on occurrence.
    '''
    def __init__(self, code = CODE_USER_REQUEST_EVENT, message = None, info = None):
        SCPIEvent.__init__(self, code, message, info)
        
class SCPIRequestControlEvent(SCPIEvent):
    '''
        A request control event.
        Bit 1 in SESR should be set on occurrence.
    '''
    def __init__(self, code = CODE_REQUEST_CONTROL_EVENT, message = None, info = None):
        SCPIEvent.__init__(self, code, message, info)
                
class SCPIOperationCompleteEvent(SCPIEvent):
    '''
        An operation complete event
        Bit 0 in SESR should be set on occurrence.
    '''
    def __init__(self, code = CODE_OPERATION_COMPLETE_EVENT, message = None, info = None):
        SCPIEvent.__init__(self, code, message, info)