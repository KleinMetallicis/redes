import socket
import json as js
import sys

def receive_full_message(connection_socket, buff_size, end_of_header):

	# recibimos la primera parte del mensaje
	recv_message = connection_socket.recv(buff_size)
	full_message = recv_message

	# verificamos si llegó el mensaje completo o si aún faltan partes del mensaje
	is_end_of_header = contains_end_of_message(full_message.decode(), end_of_header)

	# entramos a un while para recibir el resto y seguimos esperando información
	# mientras el buffer no contenga secuencia de fin de mensaje
	while not is_end_of_header:
		# recibimos un nuevo trozo del mensaje
		recv_message = connection_socket.recv(buff_size)
		
		# lo añadimos al mensaje "completo"
		full_message += recv_message

		# verificamos si es la última parte del mensaje
		is_end_of_header = contains_end_of_message(full_message.decode(), end_of_header)
	# finalmente retornamos el mensaje
	if full_message.rfind(b'Content-Length:')>=0:

		start_content_length = full_message[full_message.rfind(b'Content-Length: ') + len(b'Content-Length: '):]
		content_length = start_content_length.split(b'\r\n')
		content_length = content_length[0] 

		for i in range((int(content_length.decode())//buff_size)+1):
			recv_message = connection_socket.recv(buff_size)
			full_message += recv_message

	return full_message


def contains_end_of_message(message, end_sequence):
	return message.rfind(end_sequence) >= 0


def parse_HTTP_message(http_message:bytes):
	header_end= "\r\n\r\n"
	index = http_message.decode().rfind(header_end)
	header = http_message[:index].split(b"\r\n")
	message = http_message[(index + len(header_end)):]
	return (header, message)

def create_HTTP_message(message_pair):
	header, message = message_pair[0], message_pair[1]
	header_formed = b""
	[header_formed := header_formed + bytes(x) + b"\r\n" for x in header]

	http_message = header_formed + b"\r\n" + message
	return http_message


if __name__ == "__main__":
	# definimos el tamaño del buffer de recepción y la secuencia de fin de mensaje
	args = sys.argv
	buff_size = args[2]
	end_of_header = "\r\n\r\n"
	new_socket_address = (args[1], 8000)
	

	print('Creando socket - Servidor')
	# armamos el socket
	# los parámetros que recibe el socket indican el tipo de conexión
	# socket.SOCK_STREAM = socket orientado a conexión
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	# le indicamos al server socket que debe atender peticiones en la dirección address
	# para ello usamos bind
	server_socket.bind(new_socket_address)

	# luego con listen (función de sockets de python) le decimos que puede
	# tener hasta 3 peticiones de conexión encoladas
	# si recibiera una 4ta petición de conexión la va a rechazar
	server_socket.listen(3)

	# nos quedamos esperando a que llegue una petición de conexión
	print('... Esperando clientes')
	while True:
		# cuando llega una petición de conexión la aceptamos
		# y se crea un nuevo socket que se comunicará con el cliente
		req_socket, req_socket_address = server_socket.accept()

		# luego recibimos el mensaje usando la función que programamos
		# esta función entrega el mensaje en string (no en bytes) y sin el end_of_message
		recv_message = receive_full_message(req_socket, buff_size, end_of_header)
		
		(req_header, req_body) = parse_HTTP_message(recv_message)
		

		req_host = [match for match in req_header if b"Host:" in match]
		req_host = req_host[0]
		req_host = req_host[len(b"Host: "):]
		req_host = req_host.decode()



		#config = open("config.json", "r")
		#content = js.load(config)
		print(req_host)
		banned = open("banlist.json", "r")
		banlist = js.load(banned)
		first_line = req_header[0].decode()
		print(first_line)
		if first_line.rfind("http://") < 0:
			full_url=req_host + first_line[first_line.rfind("/"):first_line.rfind("HTTP") - 1]
		else:
			full_url = first_line[first_line.rfind("http://")+ len("http://"): first_line.rfind("HTTP/") -1]

		if full_url in banlist["blocked"]:
			
			res_header = [b'HTTP/1.1 403 Forbidden', b'Content-Type: text/html', b'Host: localhost:8000']
			res_body = "<img src=[cute-cat-say-no-with-round-background-flat-cartoon-illustration-png.png]>"
			res_header.append(b'Content-Length: ' + str(len(res_body)).encode())
			response = create_HTTP_message((res_header, res_body.encode()))
			req_socket.send(response)
			req_socket.close()
		elif full_url.rfind("[")>=0:
			res_header = [b'HTTP/1.1 200 OK', b'Content-Type: image/png', b'Host: localhost:8000']
			image_file = open("cute-cat-say-no-with-round-background-flat-cartoon-illustration-png.png","rb")
			image = image_file.read()
			length = len(image)
			res_header.append(b'Content-Length: ' + str(length).encode())
			res_body = image
			response = create_HTTP_message((res_header, res_body)) 
			req_socket.send(response)
			req_socket.close()
		else:
			
			out_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

			if req_host.rfind(":")>=0:
				req_host = req_host.split(":")
				out_socket.connect((req_host[0], int(req_host[1])))	
			else:
				out_socket.connect((req_host, 80))
			
			

			config = js.load(open("config.json" , "r"))

			req_header.append(b'X-ElQuePregunta: ' + config["nombre"].encode())
			
			out_msg= create_HTTP_message((req_header,req_body))


			out_socket.send(out_msg)
			server_response = receive_full_message(out_socket, buff_size, end_of_header)
			out_socket.close()

			(resp_head, resp_body) = parse_HTTP_message(server_response)
			
			for word in banlist["forbidden_words"]:
				key = list(word.keys())[0]

				resp_body = resp_body.replace(key.encode(), word[key].encode())
			
			server_response = create_HTTP_message((resp_head,resp_body))
			req_socket.send(server_response)
			req_socket.close()



			"""response_message= create_HTTP_message((response_header,response_body))
			
			# el mensaje debe pasarse a bytes antes de ser enviado, para ello usamos encode
			req_socket.send(response_message)

			# cerramos la conexión
			# notar que la dirección que se imprime indica un número de puerto distinto al 5000
			req_socket.close()
			print(f"conexión con {new_socket_address} ha sido cerrada")

			# seguimos esperando por si llegan otras conexiones"""