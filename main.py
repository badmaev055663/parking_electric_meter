import serial
import crcmod


ser = serial.Serial('/dev/ttyUSB0')
ser.rs485_mode
ser.timeout = 0.5
ser.baudrate = 9600

crc8 = crcmod.mkCrcFun(poly=0x1B5, initCrc=0, rev=False)

if ser.is_open == False:
        ser.open()


END = bytearray.fromhex("c0")
ESC = bytearray.fromhex("db")
OPT = bytearray.fromhex("48")

# как узнать адрес контроллера ??
src = bytearray.fromhex("0000")

# широковещание но вообще адрес счетчика - 5 последних цифр серийного номера
dst = bytearray.fromhex("ffff")


def make_requst(request_body: bytearray) -> bytearray:
	request = OPT + dst + src + request_body

	crc = hex(crc8(request))
	request = request + bytearray.fromhex(crc[2:])
	request = END + request + END

	print("request: 0x" + request.hex())
	return request

def make_request_body(data: bytearray = None) -> bytearray:
	passw = bytearray.fromhex("00000000")
	#passw = bytearray.fromhex("31de0b00")
	serv = bytes([int('11010000', 2)]) # ПОРЯДОК БИТОВ???
	addrL = bytearray.fromhex("00")
	addrH = bytearray.fromhex("01")
	request_body = passw + serv + addrL + addrH

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
	if crc != crc8(response_body):
		print("response: crc failed")
		return None

	return response_body[5:]

def parse_payload(payload: bytearray)-> bytearray:
	serv_raw = bin(payload[0])
	serv = serv_raw[2:].zfill(8)
	if serv[0] != '0' or serv[1:4] != '101':
		print("invalid serv field: " + serv)
	# собрать код команды ??
	addrH = payload[1]
	addrL = payload[2]

	data = payload[3:]
	print("data: " + data.hex())

	return data



request_body = make_request_body()
request = make_requst(request_body)

while True:
	ser.write(request)
	if KeyboardInterrupt == True:
		break
	response = ser.readline()
	payload = parse_response(response)
	if payload == None:
		print("invalid packet")
	else:
		data = parse_payload(payload)


ser.close()
