#!/usr/bin/python
# This Python file uses the following encoding: utf-8
import socket
import sys

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

    # print('Received', repr(data))
    return int(data)


def udpTransaction(host, udp_port, message):
    
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # To retrive data, send 'GET' to the server
    try:
        # print('udp port', udp_port)
        sent = udp_socket.sendto('GET', (host, udp_port))

        # Retrive data stored in server
        while 1:
            data, address = udp_socket.recvfrom(4096)
            print(data)

            # NO more messages.
            if data == 'NO MSG.':
                print('')
                break

        # The client sends its text message, over UDP, to the server.
        if message == 'TERMINATE':
            udp_socket.sendto(message, (host, udp_port))
        else:
            sent = udp_socket.sendto('[{}]: {}'.format(udp_port, message), (host, udp_port))        
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

    udp_port = tcpNegotiation(host, port, req_code)

    udpTransaction(host, udp_port, message)

    raw_input('Press any key to exit.')
    exit(0)
