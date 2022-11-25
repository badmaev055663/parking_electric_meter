import ce102


# подключение к счетчику через порт
ce102.connect("/dev/ttyUSB0")

# отправляем запрос некоторого типа с опциями и получаем
# request_type = '012F' - получить данные по электроэнергии за день
# request_type = '0130' - получить данные по электроэнергии за месяц
# request_data = '0000' - дефолтные опции 
# Подробнее опции в доке
data = ce102.send_request(request_type="0130", request_data="0000")


# парсит ответ счетчика на команду запроса энергии
# возвращает список из 4 элементов в таком порядке:
# [день, месяц, год, потраченная энергия]
if data != None:
	res = ce102.parse_get_energy_data(data)
	print(res)


# закрыть соединение
ce102.close()

