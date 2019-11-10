#!/usr/bin/env python

from packet import packet
import socket 
import sys

class Receiver():
    SEQ_NUM_MODULO = 32

    def __init__(self, host_addr, emulator_port, receiver_port, data_file_name):
        # initialize the seq_num
        current_seq_num = -1

        #create a udp socket 
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind(('', receiver_port))

        while True:
            recv_data, address = udp_socket.recvfrom(4096)
            recv_packet = packet.parse_udp_data(recv_data)
            # print('Received seq_num: ', recv_packet.seq_num, recv_packet.type, '\tcurrent seq= ', current_seq_num)

            # check if the packet is eot, if so, ack eot, then exit
            if recv_packet.type == 2:
                current_seq_num = (current_seq_num + 1)% self.SEQ_NUM_MODULO
                udp_socket.sendto(packet.create_eot(current_seq_num).get_udp_data(), (host_addr, emulator_port))
                udp_socket.close()
                exit(0)

            # Received packet, send ack
            if recv_packet.seq_num == (current_seq_num + 1)%self.SEQ_NUM_MODULO:
                current_seq_num = (current_seq_num + 1)%self.SEQ_NUM_MODULO

            # if the first packet is lost, then ack nothing
            if current_seq_num != -1:
                udp_socket.sendto(packet.create_ack(current_seq_num).get_udp_data(), (host_addr, emulator_port))

            

# Main
if __name__ == '__main__':

    if len(sys.argv) != 5:
        sys.stderr.write('Wrong arguments!\n ')
        exit(0)

    # parse argv
    host_addr = sys.argv[1]
    emulator_port = int(sys.argv[2])
    receiver_port = int(sys.argv[3])
    data_file_name = sys.argv[4]

    receiver = Receiver(host_addr, emulator_port, receiver_port, data_file_name)
    


    