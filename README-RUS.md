IEC61107
===============
Библиотека Python для работы с "умными" счётчиками, поддерживающими интерфейс протокол IEC61107 (он же ГОСТ Р МЭК 61107).

Этот протокол используется как при работе через ИК-порт (глаз) так и через RS485 или RS232.

Требования
--------------
- Python 3.7
- pyserial  (для работы через COM-порт)

Features
-------------

Поддерживается:
- Работа через аппаратный COM-порт
- Работа через мост TCP-Serial
- Программная эмуляция режима 7Е1 для COM-портов или мостов, работающих только в 8-битном режиме
- Обращение по общему адресу (только для единственного устройства на шине)
- Обращение по идентификатору
- Авторизация по паролю
- Общее чтение
- Выборочное чтение в режиме программирования

Не поддерживается:
 - Запись параметров (в любом режиме)
 - Чтение неполными блоками
 - Переключение битрейта COM-порта на лету

Установка
------------
`pip install IEC61107`

Использование
-----
Смотри следующий пример:
```python

    from IEC61107.IEC61107 import IEC61107
	from IEC61107.IEC61107 import TCP_transport
	from IEC61107.IEC61107 import Serial_transport

	#создаём транспорт, соответствующий вашему методу подключения
	transport = Serial_transport('COM3',9600,use8bits=True)
	#Для COM-портов, которые работают только в 8-битном режиме установите 
	#use8bits = True
	
	transport = TCP_transport('192.168.7.3', 12345, emulateparity = False )
    #Мост COM-TCP должен быть настроен на режим работы 7-Е-1, либо
	#Установите emulateparity в True если мост работает в 8-битном режиме
	
    #Создаём основной класс интерфейса
	mymeter = IEC61107(transport)
    
    #Начинаем сеанс обмена
    #Обращаемся к счётчику по идентификатору
	vendor, model = mymeter.init_session('155550511')
	print (vendor + ' ' + model)
    
    #Если счётчик один на шине, можно не использовать идентификатор
    # mymeter.init_session() 
    
    #Запрашиваем общее чтение
	data = mymeter.general_read()
	#Общее чтение возвращает массив строк со значениями параметров
	#список параметров зависит от счётчика
	print (data)
	#закрываем сеанс обмена
	mymeter.end_session()

    #Необходимо начать новый сеанс обмена для чтения именованных параметров после общегно чтения (ограничение протокола)
	
	vendor, model = mymeter.init_session('155550511')
	print (vendor + ' ' + model)
    
    #Переходим в режим программирования (необходимо для чтения!)
	id = mymeter.program_mode()
	#Счётчик вернёт свой идентификатор (можно его проверить)
	print(id)

    #Читаем несколько параметров
	#Точные имена параметров зависят от счётчика
	active_energy = mymeter.read_param('ET0PE')
	voltages = mymeter.read_param('VOLTA')
	currents = mymeter.read_param('CURRE')
	total_power = mymeter.read_param('POWEP')
	phase_powers = mymeter.read_param('POWPP')
	power_factor = mymeter.read_param('COS_f')
	max_power = mymeter.read_param('CMAPE')
	m_time = mymeter.read_param('TIME_')
	m_date = mymeter.read_param('DATE_')
	
	#Закрываем сеанс
	mymeter.end_session()
    
    #Каждое чтение возвращает массив строк
    
	print (active_energy)
	print (voltages)
	print (currents)
	print (phase_powers)
	print (total_power)
	print (power_factor)
	print (max_power)
	print (m_time)
	print (m_date)
	
	#gracefuly close serial or network port  
	mymeter.close()
```