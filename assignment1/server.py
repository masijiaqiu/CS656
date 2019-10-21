#!/usr/bin/python
# This Python file uses the following encoding: utf-8

# The basic tcp and udp communication is learned from online source in 
# https://docs.python.org/2/library/socket.html#socket.socket.listen 

import socket
import sys
import threading
import os

# Creates the TCP socket.
def tcpCreation():
    host = ''    
    server_port = 49311              
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, server_port))
    sock.listen(1)
    print('SERVER_PORT={}'.format(sock.getsockname()[1]))
    return sock

# Communicates over TCP. 
def tcpNegotiation(req_code, sock):
	# Builds the connection with client. 
    connection, address = sock.accept()

    while connection:
        data = connection.recv(1024)
        if not data: 
            comm_port = address[1]
            break
        # If the req_code is incorrect, reply '0' to the client. 
        # Else the server sends the client a message with a port number, which will be used for communication.
        if data != str(req_code):
            connection.sendall(str(0))
        else:
            connection.sendall(str(address[1]))
    connection.close()
    
    return sock, comm_port

# Creates the UDP socket.
def udpCreation():
    host = ''
    server_port = 49311
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind((host, server_port))
    return udp_socket

# Communicates over UDP. 
def udpTransaction(history, udp_socket):
    try: 
        while 1:
        	# Recieves messages from the client. 
            data, address = udp_socket.recvfrom(1024)

            # The server then sends all stored messages over UDP to the client.
            if data == 'GET':
                for msg in history:
                    sent = udp_socket.sendto(msg, address)

                # When there are no more messages, the server sends “​NO MSG.​”, over UDP, to the client.
                sent = udp_socket.sendto('NO MSG.', address)

            # The server gets signal to terminate the process. 
            elif data == 'TERMINATE':
                os._exit(0)

            # Adds a message to the server.
            else:
                history.append(data)
                break

    except Exception as e:
        sys.stderr.write('Error in UDP transaction.')


# Main
if __name__ == '__main__':
    tcp_socket = tcpCreation()
    udp_socket = udpCreation()
    history = list()
    try:
        while 1:
        	# Check the arguments.
            if len(sys.argv) != 2:
                sys.stderr.write('Wrong arguments!\n')
                exit(1)

            req_code = sys.argv[1]

            # Calls the function to negotiate over TCP, gets a communications port.
            main_sock, udp_port = tcpNegotiation(req_code, tcp_socket)
            # single thread process.
            # udpTransaction(history, udp_socket)

            # Multi thread handling.
            thread_handler = threading.Thread(target = udpTransaction, args = (history, udp_socket))
            thread_handler.start()
    finally:
        sock.close()
        udp_socket.close()
