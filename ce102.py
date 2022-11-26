import serial
import crcmod

crc8 = None
ser = None

def connect(port: str):
	global ser
	global crc8

	ser = serial.Serial(port)
	ser.rs485_mode
	ser.timeout = 0.7
	ser.baudrate = 9600
	crc8 = crcmod.mkCrcFun(poly=0x1B5, initCrc=0, rev=False)

	if ser.is_open == False:
		ser.open()

def close():
	ser.close()


END = bytearray.fromhex("c0")
ESC = bytearray.fromhex("db")
OPT = bytearray.fromhex("48")
PAD1 = bytearray.fromhex("dc")
PAD2 = bytearray.fromhex("dd")

# наш адрес захардкожен
src = bytearray.fromhex("0000")

# широковещание но вообще адрес счетчика - 5 последних цифр серийного номера
dst = bytearray.fromhex("ffff")

# проебразовать служебные байты в байты данных
def convert(data:bytearray)->bytearray:
	i = 0
	l = len(data)
	while i < (l - 1):
		if data[i] == ESC[0] and data[i + 1] == PAD1[0]:
			data[i:i + 2] = END
			l -= 1
		if data[i] == ESC[0] and data[i + 1] == PAD2[0]:
			data[i:i + 2] = ESC
			l -= 1
		i += 1

	return data


def make_requst(request_body: bytearray) -> bytearray:
	request = OPT + dst + src + request_body

	crc = hex(crc8(request))
	crc = crc[2:]
	if len(crc) == 1:
		crc = "0" + crc
	request = request + bytearray.fromhex(crc)
	request = END + request + END

	return request

def make_request_body(command: str, data: bytearray = None) -> bytearray:
	passw = bytearray.fromhex("00000000")
	if len(command) != 4:
		print("request: invalid command")
		return None

	if data != None:
		data_len = bin(len(data))
	else:
		data_len = bin(0)

	serv_raw = '1101' + data_len[2:].zfill(4)

	serv = bytes([int(serv_raw, 2)])
	addrL = bytearray.fromhex(command[0:2])
	addrH = bytearray.fromhex(command[2:])

	request_body = passw + serv + addrL + addrH
	if data != None:
		request_body += data

	return request_body

def parse_response(response: bytearray)-> bytearray:
	resp_len = len(response)

	# check response header: END and OPT bytes
	if response[0] != END[0] or response[resp_len - 1] != END[0]:
		print("response: " + response.hex())
		return None
	response_body = response[1:resp_len - 2]
	if response_body[0] != OPT[0]:
		print("response body: " + response_body.hex())
		return None

	# check src and dst addrs
	resp_dst = response_body[1:3]
	resp_src = response_body[3:5]
	if resp_dst != src or resp_src != dst:
		print("response: invalid addr")
		return None

	crc = response[resp_len - 2]
	response_body = convert(response_body)
	# possible trouble
	if crc != crc8(response_body):
		print("response: crc failed")
		return None

	return response_body[5:]

def parse_payload(payload: bytearray)-> bytearray:
	serv_raw = bin(payload[0])
	serv = serv_raw[2:].zfill(8)
	if serv[0] != '0' or serv[1:4] != '101':
		print("invalid serv field: " + serv)
		print("error code:", payload[3])
		return None

	# собрать код команды сделать доп проверку ??
	#addrH = payload[1]
	#addrL = payload[2]

	data = payload[3:]

	return data


def send_request(request_type: str, request_data: str = None)-> bytearray:
	if request_data != None:
		request_data_bytes = bytearray.fromhex(request_data)
		request_body = make_request_body(request_type, request_data_bytes)
	else:
		request_body = make_request_body(request_type)

	if request_body == None:
		print('failed to create request body')
		return None

	request = make_requst(request_body)
	ser.write(request)
	response = ser.readline()
	payload = parse_response(response)

	if payload == None:
		print("invalid response packet")
		return None
	else:
		data = parse_payload(payload)
		return data


def bcd_decode(bcd_byte: int)-> int:
	bcd = bin(bcd_byte)
	bcd = bcd[2:].zfill(8)
	res = int(bcd[0:4], 2) * 10
	res += int(bcd[4:], 2)
	return res


def parse_get_energy_data(data: bytearray) -> int:
	#day = bcd_decode(data[0])
	#month = bcd_decode(data[1])
	#year = bcd_decode(data[2])
	energy = int.from_bytes(data[3:], byteorder='little', signed=False)
	return energy


def get_energy_data(tariff: int, daily: bool, total: bool) -> int:
	if tariff < 0 or tariff > 5:
		print("invalid tariff:", tariff)
		return None
	if total == True:
		options = "000"
	else:
		options = "800"
	if daily == True:
		type = "012F"
	else:
		type = "0130"
	data = send_request(request_type=type, request_data=options + str(tariff))
	if data != None:
		return parse_get_energy_data(data)
	else:
		return -1
