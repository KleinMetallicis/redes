import socket

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

		start_content_length = full_message[full_message.rfind(b'Content-Length:'):]

		content_length = start_content_length[:start_content_length.rfind(b'\r\n')]
		for i in range(int(content_length)/buff_size):
			recv_message = connection_socket.recv(buff_size)
			full_message += recv_message

	return full_message


def contains_end_of_message(message, end_sequence):
	return message.endswith(end_sequence)


def remove_end_of_message(full_message, end_sequence):
	index = full_message.rfind(end_sequence)
	return full_message[:index]


def parse_HTTP_message(http_message:bytes):
	header_end= "\r\n\r\n"
	index = http_message.decode().rfind(header_end)
	(header, message) = (http_message[:index] , http_message[(index + len(header_end)):])
	return (header, message)

def create_HTTP_message(message_pair):
	header, message = message_pair[0], message_pair[1]
	http_message = header + b"\r\n\r\n" + message
	return http_message


if __name__ == "__main__":
	# definimos el tamaño del buffer de recepción y la secuencia de fin de mensaje
	buff_size = 64
	end_of_header = "\r\n\r\n"
	new_socket_address = ("localhost", 8000)
	

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
		new_socket, new_socket_address = server_socket.accept()

		# luego recibimos el mensaje usando la función que programamos
		# esta función entrega el mensaje en string (no en bytes) y sin el end_of_message
		recv_message = receive_full_message(new_socket, buff_size, end_of_header)

		print(f' -> Se ha recibido el siguiente mensaje: {recv_message}')

		(header, body) = parse_HTTP_message(recv_message)


		# respondemos indicando que recibimos el mensaje
		response_body = b"""
		<!DOCTYPE html>
		<html lang="es">
			<head>
				<meta charset="UTF-8">
				<title>Paso 1</title>
			</head>
			<body>
				<h1>Esto es un proxy?</h1>
			</body>
		</html>
		"""
		
		response_header = b"""HTTP/1.1 200 OK\r\nServer: python3.12\r\nX-ElQuePregunta: Joaquin Molina\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length:""" + str(len(response_body)).encode()
		
		response_message= create_HTTP_message((response_header,response_body))
		

		# el mensaje debe pasarse a bytes antes de ser enviado, para ello usamos encode
		new_socket.send(response_message)

		# cerramos la conexión
		# notar que la dirección que se imprime indica un número de puerto distinto al 5000
		new_socket.close()
		print(f"conexión con {new_socket_address} ha sido cerrada")

		# seguimos esperando por si llegan otras conexiones