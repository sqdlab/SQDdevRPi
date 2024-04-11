#Original author: Markus Jerger
#Created approximately: 29/09/2014
#Modified by Prasanna Pakkiam to make it compatible with Python3 and the new Raspberry Pi OS

from interface_gpio import PiGPIO
from socketserver import TCPServer, BaseRequestHandler
import os
import sys

class PiGPIOHandler(BaseRequestHandler):
    hGPIO = PiGPIO()
    
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
            # yield a line if one of the separators was found
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
        ''' pass requests to PiGPIO to handle '''
        lines = self.splitter(self.request)
        for line, separator in lines:
            head = line.split(':')[0]
            #Let the GPIO handler take care of general * commands and GPIO: commands...
            if head == 'GPIO' or line[0] == '*':
                result = PiGPIOHandler.hGPIO.process(line)
                if result:
                    self.request.send((';'.join(result)+separator).encode())
    
if __name__ == '__main__':
    # start server on all interfaces, port 4000
    HOST = ''
    PORT = 4000

    if len(sys.argv) > 0:
        tune_folder = sys.argv[1]
        file_path = f'{tune_folder}/intro.csv'
        if os.path.exists(file_path):
            os.system(f'python {os.path.dirname(os.path.realpath(__file__))}/buzzer.py 13 {file_path}')
        PiGPIOHandler.tunes_path = tune_folder

    server = TCPServer((HOST, PORT), PiGPIOHandler)
    server.serve_forever()
