import socket
import sys
import time

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
    }.get(x, 300)    # 9 is default if x not found


def calc_BCC(data):
    sum = 0;
    for byte in data:
        sum+=byte;
        sum = sum & 0xFF;
    return sum & 0x7f;

class CE301:
    def init_session(self, address = None):
        self.transport.send(StartSymbol)
        self.transport.send(ReqSymbol)
        if address is not None:
            self.transport.send(address.encode());
        self.transport.send(StopSymbol);
        self.transport.send(EndMsg);
        null,null,baudrate = self.recv_id();
        self.program_data(baudrate);
        
        rcvd_data,hdr = self.recv_data_block();
        print("Rcvd: " + rcvd_data + "Hdr " + hdr);
        self.send_password("777777");
        
    def general_read(self):
        self.read_data(baudrate);
        data_read = self.recv_data_block();
        stop_s = data_read.find(StopSymbol);
        print(data_read[:stop_s].decode());
            
    def __init__(self, transport):
        self.transport = transport
        
    def recv_id(self):
        id_msg = self.transport.recv_end(EndMsg);
        print (id_msg.decode(errors='replace'));
        start_pos = id_msg.find(StartSymbol)
        if(start_pos == -1):
            return None;
        vendor = id_msg[start_pos+1:start_pos+4].decode();
        baudrate = id_msg[start_pos+4:start_pos+5].decode();
        id = id_msg[start_pos+5:].decode();
        
        print ("vendor: " + vendor);
        print ("baudrate: " + baudrate);
        print ("id: " + id );
        return vendor, id, baudrate;
    
    def send_password(self,password):
        self.transport.send(SOHSymbol);
        data_block= bytes('P1', 'ascii');
        data_block+= STXSymbol;
        data_block+= bytes('('+password+')', 'ascii');
        data_block+= ETXSymbol;
        BCC = calc_BCC(data_block);
        self.transport.send(data_block);
        self.transport.send(bytes([BCC]));
        
        rcvd_data = self.transport.rcv(1);
        if rcvd_data == AckSymbol:
            print("Password accepted")
        else:
            print("password rejected: " + rcvd_data.hex());
    
    def read_param(self,par_name):
        self.transport.send(SOHSymbol);
        data_block= bytes('R1', 'ascii');
        data_block+= STXSymbol;
        data_block+= bytes(par_name+'()', 'ascii');
        data_block+= ETXSymbol;
        BCC = calc_BCC(data_block);
        self.transport.send(data_block);
        self.transport.send(bytes([BCC]));
        
        rcvd_data, hdr = self.recv_data_block();
        print("Rcvd: " + rcvd_data);
        return rcvd_data;
        
    def end_session(self):
        self.transport.send(SOHSymbol);
        data_block= bytes('B0', 'ascii');
        data_block+= ETXSymbol;
        BCC = calc_BCC(data_block);
        self.transport.send(data_block);
        self.transport.send(bytes([BCC]));
        
    def recv_data_block(self):
        block = self.transport.recv_end(ETXSymbol);
        BCC   = self.transport.rcv(1);
        
        hdr_start = block.find(SOHSymbol);
        header = None
        
        msg_start = block.find(STXSymbol);
        
        if(hdr_start >=0):
            header = block[hdr_start+1:msg_start].decode();
        else:
            hdr_start = msg_start;
            
        bytes_for_bcc = block[hdr_start+1:]+ETXSymbol
        
        calculated_BCC = calc_BCC(bytes_for_bcc);
        
        #todo: check BCC
        
        return block[msg_start+1:].decode(),header
        
        
    def read_data(self,baud):
        self.transport.send(AckSymbol)
        self.transport.send(bytes('0', 'ascii')) #normal mode
        self.transport.send(bytes(baud,'ascii'))
        self.transport.send(bytes('0', 'ascii')) #read mode
        self.transport.send(EndMsg)
    
    def program_data(self,baud):
        self.transport.send(AckSymbol)
        self.transport.send(bytes('0', 'ascii')) #normal mode
        self.transport.send(bytes(baud,'ascii'))
        self.transport.send(bytes('1', 'ascii')) #program mode
        self.transport.send(EndMsg)


def parity_kr(n):
    parity = 0
    while n: 
        parity = ~parity 
        n = n & (n - 1) 
    return parity 

class CE_transport:
    remains = None;
    def __init__(self,address,port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((address,port))
        self.sock.settimeout(10.0)
    
    def send(self, bytes_snd):
        #print("Sending")
        #print(bytes_snd.hex())
        paritybytes = bytearray() 
        for byte in bytes_snd:
            parity = parity_kr(byte)
            if(parity != 0):
                byte = byte | 0x80;
            paritybytes.append(byte)
        #print("As")
        #print(paritybytes.hex())
        self.sock.sendall(paritybytes)
    
    def rcv(self, maxsize = 255):
            data_noparity = bytearray();
            if self.remains is not None:
                if len(self.remains) == maxsize:
                    data_noparity = self.remains;
                    self.remains = None;
                    #print("remains exactly")
                    return data_noparity;
                elif len(self.remains) < maxsize:
                    #print("remains less")
                    data_noparity += self.remains;
                else:
                    #print("remains more")
                    data_noparity = self.remains[:maxsize]
                    remains = self.remains[maxsize:];
                    return data_noparity;
             
            data = self.sock.recv(maxsize)
            
            for byte in data:
                byte = byte & 0x7f
                data_noparity.append(byte)
            return data_noparity;
            
    def recv_end(self, End):
        total_data=bytearray();
        while True:
                data_noparity = self.rcv();
                
                if End in data_noparity:
                    endplace = data_noparity.find(End);
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
        
        
    
    
    