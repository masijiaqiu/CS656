#!/usr/bin/python
# This Python file uses the following encoding: utf-8

# The basic tcp and udp communication is learned from online source in 
# https://docs.python.org/2/library/socket.html#socket.socket.listen 

import socket
import sys

# Communicates with the server over TCP
def tcpNegotiation(host, port, req_code):
    # The client creates a TCP socket and connects to the server.
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    # The client sends a message to the server containing a numerical code
    sock.sendall(str(req_code))

    data = sock.recv(1024)
    sock.close()

    if data == '0':
        print('Invalid req_code.')
        exit(1)

    return int(data)

# Communicates with the server over UDP
def udpTransaction(host, client_port, message):
    server_port = 49311
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # To retrive data, send 'GET' to the server
    try:
        sent = udp_socket.sendto('GET', (host, server_port))

        # Retrive data stored in server
        while 1:
            data, address = udp_socket.recvfrom(1024)
            print(data)
            # NO more messages.
            if data == 'NO MSG.':
                print('')
                break

        # The client sends its text message, over UDP, to the server.
        if message == 'TERMINATE':
            udp_socket.sendto(message, (host, server_port))
        else:
            sent = udp_socket.sendto('[{}]: {}'.format(client_port, message), (host, server_port))        
    finally:
        udp_socket.close()
    return 0


if __name__ == '__main__':
    if len(sys.argv) != 5:
        sys.stderr.write('Wrong arguments!\n')
    host = sys.argv[1]
    port = int(sys.argv[2])
    req_code = int(sys.argv[3])
    message = sys.argv[4]

    client_port = tcpNegotiation(host, port, req_code)

    udpTransaction(host, client_port, message)

    raw_input('Press any key to exit.')
    exit(0)
