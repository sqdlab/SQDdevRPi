#Original author: Markus Jerger
#Created approximately: 29/09/2014
#Modified by Prasanna Pakkiam to make it compatible with Python3 and the new Raspberry Pi OS
#Modified by Stephen Fowler to add USB compatibility: 07/02/2025

# sudo lsof -t -i:4000 | xargs sudo kill -9
      
from interface_gpio import PiGPIO
from socketserver import TCPServer, BaseRequestHandler
import os
import subprocess
import sys

from interface_usb import PiUSB
class PiUSBandGPIOHandler(BaseRequestHandler):
    hGPIO = PiGPIO()
    hUSB = PiUSB(debugging=True)

    
    def splitter(self, request, separators = ['\r\n', '\n']):
        ''' split data received from a socket into lines '''
        data = ''
        while True:
            # receive input data
            data_block = self.request.recv(1024)
            if not data_block:
                # the connection has been closed and all data has been received
                # any unterminated lines in data are ignored
                return
            data = data + data_block.decode()
            # yield a line if one of the separators was found\n #test
            # assumes that line separators do not change
            for separator in separators:
                while True:
                    idx = data.find(separator)
                    if(idx == -1):
                        break
                    else:
                        yield (data[:idx], separator)
                        data = data[(idx+len(separator)):]
        
    def handle(self):
        ''' pass requests to PiUSB PiGPIO to handle '''
        print("request passed to handler:" , self.request)
        lines = self.splitter(self.request)
        for line, separator in lines:
            head = line.split(':')[0]
            #Let the GPIO handler take care of general * commands and GPIO: commands...
            if head == 'USB':
                result = PiUSBandGPIOHandler.hUSB.process(line)
                if result:
                    self.request.send((';'.join(result)+separator).encode())
                    print("handled ran")
            elif head == 'GPIO' or line[0] == '*':
                result = PiUSBandGPIOHandler.hGPIO.process(line)
                if result:
                    self.request.send((';'.join(result)+separator).encode())
    
if __name__ == '__main__':
    # If recieving a OSError: [Errno 98] Address already in use after restarting the program:
    #                       1. Ensure both host and client have stopped running.
    #                       2. On Pi, enter:    sudo lsof -t -i:4000 | xargs sudo kill -9

    HOST = ''
    PORT = 4000

    if len(sys.argv) > 1:
        tune_folder = sys.argv[1]
        file_path = f'{tune_folder}/intro.csv'
        if os.path.exists(file_path):
            subprocess.Popen([f'python', f'{os.path.dirname(os.path.realpath(__file__))}/buzzer.py', '13', file_path])
        PiGPIO.tunes_path = tune_folder


    with TCPServer((HOST, PORT), PiUSBandGPIOHandler) as server:
        server.serve_forever()
