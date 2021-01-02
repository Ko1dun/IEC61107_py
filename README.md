IEC61107
===============
Python library for interfacing with smart meters supporting IEC61107 protocol 

Requirements
--------------
Python 3.7
pyserial

Features
-------------

Supported:
- Hardware serial port
- Network-to-serial (TCP)
- Parity emulation for serial devices not capable of 7-E-1 mode
- broadcast addressing (for single device on a bus)
- addressing by ID
- password authentication
- generic readout
- named parameters readout

Not supported:
 - all programming modes
 - non-full blocks read
 - baudrate switching on-the-fly

Installation
------------
`pip install IEC61107`

Usage
-----
See following python example
```python
    from IEC61107 import IEC61107
	from IEC61107 import TCP_transport
	from IEC61107 import Serial_transport

#create transport matching you connection method
	transport = Serial_transport('COM3',9600,use8bits=True)
	#for serial devices not supporting 7 bit mode set 
	#use8bits = True
	
	transport = TCP_transport('192.168.7.3', 12345, emulateparity = False )
    #set emulateparity to True if your network-to-serial bridge can not work in 7 bit mode

    #create main interface class
	mymeter = IEC61107(transport)
    
    #start excjange session
    #address meter by its ID
	vendor, model = mymeter.init_session('155550511')
	print (vendor + ' ' + model)
    
    #if you have only one device on a bus, you can omit ID 
    # mymeter.init_session() 
    
    #request generic read
	data = mymeter.general_read()
	#generic read returns an array of strings with parameter`s values
	#parameter list is device-specific
	print (data)
	#close exchange session
	mymeter.end_session()

    #you need to start a new session in order to read named parameters (protocol limit)
	vendor, model = mymeter.init_session('155550511')
	print (vendor + ' ' + model)
    
    #switch meter to program mode (needed for readout!)
	id = mymeter.program_mode()
	#meter should respond with its ID. you can check it
	print(id)

    #read some parameters:
	active_energy = mymeter.read_param('ET0PE')
	voltages = mymeter.read_param('VOLTA')
	currents = mymeter.read_param('CURRE')
	total_power = mymeter.read_param('POWEP')
	phase_powers = mymeter.read_param('POWPP')
	power_factor = mymeter.read_param('COS_f')
	max_power = mymeter.read_param('CMAPE')
	m_time = mymeter.read_param('TIME_')
	m_date = mymeter.read_param('DATE_')
	
	#close session
	mymeter.end_session()
    
    #each read returns an array of strings  
    
	print (active_energy)
	print (voltages)
	print (currents)
	print (phase_powers)
	print (total_power)
	print (power_factor)
	print (max_power)
	print (m_time)
	print (m_date)
```