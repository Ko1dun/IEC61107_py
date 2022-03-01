import socket
import sys
import time
import serial
import re

StartSymbol = bytes('/','ascii')
StopSymbol  = bytes('!','ascii')
ReqSymbol   = bytes('?','ascii')
AckSymbol   = bytes([0x06])
SOHSymbol   = bytes([0x01])
STXSymbol   = bytes([0x02])
ETXSymbol   = bytes([0x03])
EOTSymbol   = bytes([0x04])
EndMsg      = bytes('\r\n','ascii')

def baud_decode(x):
    return {
        '0': 300,
        '1': 600,
        '2': 1200,
        '3': 2400,
        '4': 4800,
        '5': 9600,
        
        'A': 600,
        'B': 1200,
        'C': 2400,
        'D': 4800,
        'E': 9600,
    }.get(x, 300)  


def calc_BCC(data):
    sum = 0
    for byte in data:
        sum+=byte
        sum = sum & 0xFF
    return sum & 0x7f

def parse_param_array(str):
    params = []
    lines = str.splitlines()
    for line in lines:
        params.append(line[line.find('(')+1:line.rfind(')')])
    return params
    
def parse_name_param_array(str):
    params = []
    lines = str.splitlines()
    prev_name  = ''
    for line in lines:
        par = line[line.find('(')+1:line.rfind(')')]
        name = line[:line.find('(')]
        if not name:
            name = prev_name
        else:
            prev_name = name
            
        params.append([name,par])
    return params

class IEC61107:
    baudrate = None
    def __init__(self, transport):
        self.transport = transport
        
    def init_session(self, address = None):
        self.transport.open()
        self.transport.send(StartSymbol)
        self.transport.send(ReqSymbol)
        if address is not None:
            self.transport.send(address.encode())
        self.transport.send(StopSymbol)
        self.transport.send(EndMsg)
        vendor,id = self.recv_id()
        return vendor,id

    def general_read(self):
        self.read_data()
        data, hdr = self.recv_data_block()
        data = data.rstrip((EndMsg + StopSymbol).decode())
        return parse_name_param_array(data)

    def program_mode(self):
        self.program_data()
        rcvd_data, hdr = self.recv_data_block()
        addr = rcvd_data.lstrip('(').rstrip(')');
        return addr;
          
    def recv_id(self):
        id_msg = self.transport.recv_end(EndMsg)
        start_pos = id_msg.find(StartSymbol)
        if start_pos == -1:
            return None
        vendor = id_msg[start_pos+1:start_pos+4].decode()
        self.baudrate = id_msg[start_pos+4:start_pos+5].decode()
        id = id_msg[start_pos+5:].decode()

        return vendor, id
    
    def authorize(self, password):
        self.transport.send(SOHSymbol)
        data_block= bytes('P1', 'ascii')
        data_block+= STXSymbol
        data_block+= bytes('('+password+')', 'ascii')
        data_block+= ETXSymbol
        bcc = calc_BCC(data_block)
        self.transport.send(data_block)
        self.transport.send(bytes([bcc]))
        
        rcvd_data = self.transport.rcv(1)
        if rcvd_data == AckSymbol:
            print("Password accepted")
        else:
            print("password rejected: " + rcvd_data.hex())
    
    def read_param(self,par_name):
        self.transport.send(SOHSymbol)
        data_block= bytes('R1', 'ascii')
        data_block+= STXSymbol
        data_block+= bytes(par_name+'()', 'ascii')
        data_block+= ETXSymbol
        bcc = calc_BCC(data_block)
        self.transport.send(data_block)
        self.transport.send(bytes([bcc]))
        
        rcvd_data, hdr = self.recv_data_block()
        
        return parse_param_array(rcvd_data)
        
    def end_session(self):
        self.transport.send(SOHSymbol)
        data_block= bytes('B0', 'ascii')
        data_block+= ETXSymbol
        bcc = calc_BCC(data_block)
        self.transport.send(data_block)
        self.transport.send(bytes([bcc]))
        time.sleep(2)
                      
    def recv_data_block(self):
        block = self.transport.recv_end(ETXSymbol)
        bcc   = self.transport.rcv(1)

        hdr_start = block.find(SOHSymbol)
        header = None
        
        msg_start = block.find(STXSymbol)

        if(hdr_start >=0):
            header = block[hdr_start+1:msg_start].decode()
        else:
            hdr_start = msg_start

        bytes_for_bcc = block[hdr_start+1:]+ETXSymbol
        
        calculated_BCC = calc_BCC(bytes_for_bcc)
        
        #todo: check BCC
        
        return block[msg_start+1:].decode(),header
        
        
    def read_data(self):
        self.transport.send(AckSymbol)
        self.transport.send(bytes('0', 'ascii')) #normal mode
        self.transport.send(bytes(self.baudrate,'ascii'))
        self.transport.send(bytes('0', 'ascii')) #read mode
        self.transport.send(EndMsg)
    
    def program_data(self):
        self.transport.send(AckSymbol)
        self.transport.send(bytes('0', 'ascii')) #normal mode
        self.transport.send(bytes(self.baudrate,'ascii'))
        self.transport.send(bytes('1', 'ascii')) #program mode
        self.transport.send(EndMsg)
        
    def close(self):
        self.transport.close()


def parity_calc(n):
    parity = 0
    while n: 
        parity = ~parity 
        n = n & (n - 1) 
    return parity 

class TCP_transport:
    remains = None
    softparity = True
    def __init__(self,address,port,emulateparity = True):
        self.opened = False
        self.address = address
        self.port = port
        self.softparity = emulateparity
    
    def open(self):
        if self.opened == False:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.address,self.port))
            self.sock.settimeout(10.0)
            self.opened = True
    
    def send(self, bytes_snd):
        if self.softparity == True:
            paritybytes = bytearray()
            for byte in bytes_snd:
                parity = parity_calc(byte)
                if(parity != 0):
                    byte = byte | 0x80
                paritybytes.append(byte)
            self.sock.sendall(paritybytes)
        else:
            self.sock.sendall(bytes_snd)
    
    def rcv(self, maxsize = 255):
        data_noparity = bytearray()
        if self.remains is not None:
            if len(self.remains) == maxsize:
                data_noparity = self.remains
                self.remains = None
                return data_noparity
            elif len(self.remains) < maxsize:
                data_noparity += self.remains
            else:
                data_noparity = self.remains[:maxsize]
                remains = self.remains[maxsize:]
                return data_noparity

        data = self.sock.recv(maxsize)

        for byte in data:
            byte = byte & 0x7f
            data_noparity.append(byte)
        return data_noparity

    def recv_end(self, End):
        total_data=bytearray()
        while True:
                data_noparity = self.rcv()

                if End in data_noparity:
                    endplace = data_noparity.find(End)
                    #print (endplace);
                    #print (len(data_noparity));
                    if endplace+len(End) < len(data_noparity):
                        self.remains = data_noparity[endplace+len(End):]
                        #print (self.remains.hex())
                    total_data+=(data_noparity[:data_noparity.find(End)])
                    break
                total_data+=(data_noparity)
                
                if len(total_data)>1:
                    if End in total_data:
                        endplace = total_data.find(End)
                        #print (endplace);
                        #print (len(total_data));
                        if endplace+len(End) < len(total_data):
                            self.remains = total_data[endplace+len(End):]
                            #print (self.remains.hex())
                        return total_data[:endplace]
                        break
            
        return total_data
        
    def close(self):
        self.sock.close()
        self.opened = False

        
class Serial_transport:
    remains = None
    softparity = False
    def __init__(self,port,baudrate,use8bits=False):
        self.opened = False
        if use8bits == False:
            #Open serial in 7-E-1 mode
            self.softparity = False;
            self.serial_port = serial.Serial(port, baudrate, timeout=10.0,
                        parity=serial.PARITY_EVEN, bytesize=serial.SEVENBITS )
            self.opened = True
        else:
            #open in 8-N-1 mode and calculate parity in software
            self.softparity = True
            self.serial_port = serial.Serial(port, baudrate, timeout=10.0,
                                     parity=serial.PARITY_NONE, bytesize=serial.EIGHTBITS)
            self.opened = True
    
    def open(self):
        if not self.opened:
            self.serial_port.open()
            self.opened = True
       
    def send(self, bytes_snd):
        if self.softparity == True:
            paritybytes = bytearray()
            for byte in bytes_snd:
                parity = parity_calc(byte)
                if (parity != 0):
                    byte = byte | 0x80
                paritybytes.append(byte)
            self.serial_port.write(paritybytes)
        else:
            self.serial_port.write(bytes_snd)

    def rcv(self, maxsize=255):
        data_noparity = bytearray()
        if self.remains is not None:
            if len(self.remains) == maxsize:
                data_noparity = self.remains
                self.remains = None
                # print("remains exactly")
                return data_noparity
            elif len(self.remains) < maxsize:
                # print("remains less")
                data_noparity += self.remains
            else:
                # print("remains more")
                data_noparity = self.remains[:maxsize]
                remains = self.remains[maxsize:]
                return data_noparity

        data = self.serial_port.read(maxsize)

        for byte in data:
            byte = byte & 0x7f
            data_noparity.append(byte)
        return data_noparity

    def recv_end(self, End):
        total_data = bytearray()
        while True:
            data_noparity = self.rcv()
            
            if len(data_noparity) == 0:
                raise TimeoutError('No data received');

            if End in data_noparity:
                endplace = data_noparity.find(End)
                if endplace + len(End) < len(data_noparity):
                    self.remains = data_noparity[endplace + len(End):]
                total_data += (data_noparity[:data_noparity.find(End)])
                break
            total_data += (data_noparity)

            if len(total_data) > 1:
                if End in total_data:
                    endplace = total_data.find(End)
                    if endplace + len(End) < len(total_data):
                        self.remains = total_data[endplace + len(End):]
                    return total_data[:endplace]
                    break

        return total_data
        
    def close(self):
        if self.opened :
            self.serial_port.close()
            self.opened = False
    