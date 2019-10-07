#!/usr/bin/python
# This Python file uses the following encoding: utf-8

# https://docs.python.org/2/library/socket.html#socket.socket.listen 

import socket
import sys
import threading
import os


def tcpCreation():
    host = ''    
    port = 9061              
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, port))
    sock.listen(5)
    print('SERVER_PORT={}'.format(sock.getsockname()[1]))
    return sock

def tcpNegotiation(req_code, sock):
    connection, address = sock.accept()

    while connection:
        data = connection.recv(1024)
        if not data: 
            comm_port = address[1]
            break
        if data != str(req_code):
            connection.sendall(str(0))
        else:
            connection.sendall(str(address[1]))
    connection.close()
    
    return sock, comm_port


def udpTransaction(port):
    host = ''
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind((host, port))
    try: 
        while 1:
            data, address = udp_socket.recvfrom(4096)

            # The server then sends all stored messages over UDP to the client.
            if data == 'GET':
                
                for msg in history:
                    sent = udp_socket.sendto(msg, address)

                # When there are no more messages, the server sends “​NO MSG.​”, over UDP, to the client.
                sent = udp_socket.sendto('NO MSG.', address)


            elif data == 'TERMINATE':
                os._exit(0)
            else:
                history.append(data)
                break
    finally:
        udp_socket.close()



history = list()
if __name__ == '__main__':
    sock = tcpCreation()
    
    while 1:
        if len(sys.argv) != 2:
            sys.stderr.write('Wrong arguments!\n')
            exit(1)
        
        req_code = sys.argv[1]
        
        main_sock, udp_port = tcpNegotiation(req_code, sock)
        # udpTransaction(udp_port)

        thread_handler = threading.Thread(target = udpTransaction, args = (udp_port,))
        thread_handler.start()
