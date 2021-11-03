#!/bin/python3
import socket, sys, threading

server_ip = '127.0.0.2'
server_port = 9993
SERV_RESPONSE_SIZE = 4096

#hostname, sld, tld, port = 'www', 'integralist', 'co.uk', 80
hostname, sld, tld, port = 'www', 'tecnico', 'ulisboa.pt', 80
target = '{}.{}.{}'.format(hostname, sld, tld)
print ('target', target)

#this funciton processes the server response
def process_server_response(server_response):
	msg_from_server = server_response.decode()
	print(msg_from_server)
#func end

#main
def main():
	# create an ipv4 (AF_INET) socket object using the tcp protocol (SOCK_STREAM)
	client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		# connect the client
		# client.connect((target, port))
		client.connect((server_ip, server_port))
	except:
		print("server dead")
		client.close()
		exit(1)
	
	while(True):
		client_input = sys.stdin.readline()
		if(client_input != None):
			toSend = client_input
			client.send(toSend.encode())
			server_response = client.recv(SERV_RESPONSE_SIZE)
			process_server_response(server_response)
#func end
	
if(__name__ == '__main__'):
	main()
#func end