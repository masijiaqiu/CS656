#!/usr/bin/env python

from packet import packet
import socket
import sys
from collections import deque
import time
from threading import Thread
import threading
import os

class Sender():
    WINDOW_SIZE = 10
    MAX_DATA_LENGTH = 500
    SEQ_NUM_MODULO = 32
    TIMEOUT = 0.1

    def __init__(self, host_addr, emulator_port, sender_port, data_file_path):
        self.packets_list = list()
        self.host_addr = host_addr
        self.emulator_port = emulator_port
        self.sender_port = sender_port

        self.lock = threading.Lock()

        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind(('', sender_port))

        self.next_ack = 0

        self.seqnum_log = list()
        self.time_log = list()
        self.ack_log = list()

        self.seqnum_log_file = open('seqnum.log', 'w')
        self.ack_log_file = open('ack.log', 'w')
        self.time_log_file = open('time.log', 'w')
        
        seq_num = 0
        with open(data_file_path, 'r') as f:
            chunk = f.read(self.MAX_DATA_LENGTH)
            while chunk:
                self.packets_list.append(packet.create_packet(seq_num, chunk))

                seq_num += 1
                chunk = f.read(self.MAX_DATA_LENGTH)
            # self.packets_list.append(packet.create_eot(seq_num))

        print("Number of data packets is: " + str(len(self.packets_list)))

        # Initlialize the sliding window 
        self.sliding_window = list()
        if len(self.packets_list) < self.WINDOW_SIZE:
            self.sliding_window.extend(self.packets_list)
        else:
            self.sliding_window.extend(self.packets_list[:self.WINDOW_SIZE])
            self.packets_list = self.packets_list[self.WINDOW_SIZE:]


    def receive(self):
        while True:
            recv_data, address = self.udp_socket.recvfrom(4096)
            recv_packet = packet.parse_udp_data(recv_data)
            # print('recv ack: ', recv_packet.seq_num)
            self.ack_log.append(recv_packet.seq_num)

            if recv_packet.type == 2:
                self.time_log.append(time.time())
                # print('EOT. WRITE LOG.')

                for ack in self.ack_log:
                    self.ack_log_file.write(str(ack) + '\n')
                self.ack_log_file.close()
                
                print(self.time_log[1] - self.time_log[0])
                self.time_log_file.write(str(abs(self.time_log[1] - self.time_log[0])))
                self.time_log_file.close()

                for num in self.seqnum_log:
                    self.seqnum_log_file.write(str(num) + '\n')
                self.seqnum_log_file.close()
                # print('ack_log:', self.ack_log)
                # print('time_log:', self.time_log[1] - self.time_log[0])
                # print('seqnum_log:', self.seqnum_log)

                os._exit(0)

            self.lock.acquire()

            if (self.next_ack + self.WINDOW_SIZE)%self.SEQ_NUM_MODULO > self.next_ack:
                if recv_packet.seq_num >= self.next_ack and recv_packet.seq_num < self.next_ack + self.WINDOW_SIZE:
                    self.next_ack = (recv_packet.seq_num + 1) % self.SEQ_NUM_MODULO
            else:
                if recv_packet.seq_num >= self.next_ack or recv_packet.seq_num < (self.next_ack + self.WINDOW_SIZE)%self.SEQ_NUM_MODULO:
                    self.next_ack = (recv_packet.seq_num + 1) % self.SEQ_NUM_MODULO
            self.lock.release()



            
    def send(self):
        
        cur_ack = 0
        foo = 0
        start_time = time.time()
        pack_sent = 0 # how many pack in the sliding window are sent

        self.time_log.append(time.time())

        for pack in self.sliding_window:
            self.udp_socket.sendto(pack.get_udp_data(), (self.host_addr, self.emulator_port))
            pack_sent += 1
            self.seqnum_log.append(pack.seq_num)

        while len(self.sliding_window) != 0 or len(self.packets_list) != 0:

            while time.time() - start_time < self.TIMEOUT:
                if cur_ack != self.next_ack:
                    

                    start_time = time.time()
                    self.lock.acquire()
                    
                    print('move_window', 'cur_ack=',cur_ack,' ', ' next_ack=', self.next_ack, ' pack_sent=', pack_sent)

                    for _ in range((self.next_ack - cur_ack)%self.SEQ_NUM_MODULO):
                        self.sliding_window.pop(0)
                        pack_sent -= 1
                        # print('pack_sent -= 1')
                        if len(self.packets_list) != 0:
                            self.sliding_window.append(self.packets_list.pop(0))

                    cur_ack = self.next_ack     
                    # print('len packet list=', len(self.packets_list))
                    

                    if pack_sent < len(self.sliding_window):
                        for pack in self.sliding_window[pack_sent:]:
                            print('send pack ++', pack.seq_num)
                            self.udp_socket.sendto(pack.get_udp_data(), (self.host_addr, self.emulator_port))
                            pack_sent += 1
                            self.seqnum_log.append(pack.seq_num)
                    self.lock.release()


            start_time = time.time()
            print('TIMEOUT: self.next_ack', self.next_ack)

            # self.lock.acquire()
            for pack in self.sliding_window:
                self.udp_socket.sendto(pack.get_udp_data(), (self.host_addr, self.emulator_port))
                self.seqnum_log.append(pack.seq_num)
                # print('timeout send: ', pack.seq_num)
            # self.lock.release()

        # Send all the content 
        # print('SEND EOT', self.next_ack)
        self.udp_socket.sendto(packet.create_eot(self.next_ack).get_udp_data(), (self.host_addr, self.emulator_port))
                

# Main
if __name__ == '__main__':

    if len(sys.argv) != 5:
        sys.stderr.write('Wrong arguments!\n Valid format: <host_addr> <emulator_port> <sender_port> <data_file>\n')
        exit(0)

    # parse argv
    host_addr = sys.argv[1]
    emulator_port = int(sys.argv[2])
    sender_port = int(sys.argv[3])
    data_file_path = sys.argv[4]

    sender = Sender(host_addr, emulator_port, sender_port, data_file_path)

    send_thread = Thread(target=sender.send, args=())
    recv_thread = Thread(target=sender.receive, args=())

    recv_thread.start()
    send_thread.start()

