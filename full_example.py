from IEC61107.IEC61107 import IEC61107
from IEC61107.IEC61107 import TCP_transport
from IEC61107.IEC61107 import Serial_transport

transport = TCP_transport('192.168.7.3', 12345)
#transport = Serial_transport('COM3',9600,use8bits=True)

mymeter = IEC61107(transport)

vendor, model = mymeter.init_session('111111111')
print (vendor + ' ' + model)

data = mymeter.general_read()
print (data)
mymeter.end_session()

vendor, model = mymeter.init_session('111111111')
print (vendor + ' ' + model)

addr = mymeter.program_mode()
print(addr)

active_energy = mymeter.read_param('ET0PE')
voltages = mymeter.read_param('VOLTA')
currents = mymeter.read_param('CURRE')
total_power = mymeter.read_param('POWEP')
phase_powers = mymeter.read_param('POWPP')
power_factor = mymeter.read_param('COS_f')
max_power = mymeter.read_param('CMAPE')
m_time = mymeter.read_param('TIME_')
m_date = mymeter.read_param('DATE_')
mymeter.end_session()

print (active_energy)
print (voltages)
print (currents)
print (phase_powers)
print (total_power)
print (power_factor)
print (max_power)
print (m_time)
print (m_date)

mymeter.close()