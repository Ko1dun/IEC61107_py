from ce301 import CE301
from ce301 import CE_transport

transport = CE_transport('192.168.7.3',12345)

mymeter = CE301(transport)

print("Hello py!")

mymeter.init_session()
mymeter.read_param('ET0PE')
mymeter.read_param('VOLTA')
mymeter.read_param('CURRE')
mymeter.read_param('POWEP')
mymeter.read_param('POWPP')
mymeter.end_session()