from IEC61107.IEC61107 import IEC61107
from IEC61107.IEC61107 import TCP_transport

transport = TCP_transport('192.168.7.3', 12345)
mymeter = IEC61107(transport)

mymeter.init_session()
data = mymeter.general_read()
mymeter.end_session()
mymeter.close()

print ("Total energy(kWh): " + data[0])