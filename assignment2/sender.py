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

        
        seq_num = 0
        with open(data_file_path, 'r') as f:
            chunk = f.read(self.MAX_DATA_LENGTH)
            while chunk:
                self.packets_list.append(packet.create_packet(seq_num, chunk))

                seq_num += 1
                chunk = f.read(self.MAX_DATA_LENGTH)
            self.packets_list.append(packet.create_eot(seq_num))

        print("Number of packets is: " + str(len(self.packets_list)))

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
                print('EOT')
                print('ack_log:', self.ack_log)
                print('time_log:', self.time_log[1] - self.time_log[0])
                print('seqnum_log:', self.seqnum_log)

                os._exit(0)
                break

            self.lock.acquire()

            if (self.next_ack + self.WINDOW_SIZE)%self.SEQ_NUM_MODULO > self.next_ack:
                if recv_packet.seq_num >= self.next_ack and recv_packet.seq_num < self.next_ack + self.WINDOW_SIZE:
                    self.next_ack = (self.next_ack + 1) % self.SEQ_NUM_MODULO
            else:
                if recv_packet.seq_num >= self.next_ack or recv_packet.seq_num < (self.next_ack + self.WINDOW_SIZE)%self.SEQ_NUM_MODULO:
                    self.next_ack = (self.next_ack + 1) % self.SEQ_NUM_MODULO
            self.lock.release()
            # print('self.next_ack', self.next_ack)
            
            # if self.next_ack == recv_packet.seq_num:
            #     self.lock.acquire()
            #     self.next_ack = (self.next_ack + 1) % self.SEQ_NUM_MODULO
            #     self.lock.release()

            #     self.sliding_window.pop(0)
            #     if len(self.packets_list) != 0:
            #         self.sliding_window.append(self.packets_list.pop(0))

            
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

        while len(self.sliding_window) != 0 and len(self.packets_list) != 0:
            # start a timer
            
            # foo += 1
            # print('sender: ', len(self.sliding_window), foo)

            while time.time() - start_time < self.TIMEOUT:
                if cur_ack != self.next_ack:
                    

                    start_time = time.time()
                    self.lock.acquire()
                    # for i in range(len(self.sliding_window)):
                    #     if (self.sliding_window[i].seq_num + 1) % self.SEQ_NUM_MODULO == self.next_ack and len(self.packets_list) != 0:
                    #         for _ in range(i):
                    #             self.sliding_window.pop(0)
                    #             print('pack_sent -= 1')
                    #             pack_sent -= 1
                    #             if len(self.packets_list) != 0:
                    #                 self.sliding_window.append(self.packets_list.pop(0))
                    # print('move_window', 'cur_ack=',cur_ack,' ', ' next_ack=', self.next_ack, ' pack_sent=', pack_sent)
                    
                    for _ in range((self.next_ack - cur_ack)%32):
                        self.sliding_window.pop(0)
                        pack_sent -= 1
                        # print('pack_sent -= 1')
                        if len(self.packets_list) != 0:
                            self.sliding_window.append(self.packets_list.pop(0))

                    cur_ack = self.next_ack     
                    # print('len packet list=', len(self.packets_list))
                    

                    if pack_sent < len(self.sliding_window):
                        # for pack in self.sliding_window[pack_sent:]:
                        #     print('send pack ++', pack.seq_num)
                            self.udp_socket.sendto(pack.get_udp_data(), (self.host_addr, self.emulator_port))
                            pack_sent += 1
                            self.seqnum_log.append(pack.seq_num)
                    self.lock.release()




            # while time.time() - start_time < self.TIMEOUT:
            #     if cur_ack == self.next_ack:
            #         pass
            #     else:
            #         start_time = time.time()
            #         pack_sent = self.next_ack - 
            #         if pack_sent <= self.WINDOW_SIZE:
            #             for pack in self.sliding_window[pack_sent:]:


            # # resend every packet in the sliding window
               # self.lock.acquire()
            # for pack in self.sliding_window:
            #     self.udp_socket.sendto(pack.get_udp_data(), ('',10001))
            #     pack_sent = (pack_sent + 1)% self.SEQ_NUM_MODULO
                
            # self.lock.release()


            # Time out. Re-send packets in the sliding window
            # self.lock.acquire()
            start_time = time.time()
            # print('TIMEOUT: self.next_ack', self.next_ack)

            # self.lock.acquire()
            for pack in self.sliding_window:
                self.udp_socket.sendto(pack.get_udp_data(), (self.host_addr, self.emulator_port))
                self.seqnum_log.append(pack.seq_num)
                # print('timeout send: ', pack.seq_num)
            # self.lock.release()

            # while time.time() - start_time < self.TIMEOUT:
            #     if self.next_ack == cur_ack:
            #         pass
            #     else:


#####################################################################

            # if time.time() - start_time > self.TIMEOUT:
            #     print('TIMEOUT')
            #     # resend everything
            #     pack_sent = 0
            #     for pack in self.sliding_window:
            #         self.udp_socket.sendto(pack.get_udp_data(), ('',10001))
            #         print('send pkt', pack.seq_num)
            #         pack_sent += 1
            #     start_time = time.time()

            
            # elif self.next_ack != cur_ack:
            #     print('send, cur_ack:',cur_ack, 'pack_sent', pack_sent)
            #     if cur_ack == None:
            #         cur_ack = 0
            #     acked_pack_count = (self.next_ack - cur_ack) % 32
            #     cur_ack = self.next_ack
            #     if pack_sent - acked_pack_count > 0:
            #         pack_sent -= acked_pack_count
            #     else:
            #         pack_sent = 0
            #     for pack in self.sliding_window[pack_sent:]:
            #         self.udp_socket.sendto(pack.get_udp_data(), ('',10001))
            #         pack_sent += 1

            #     start_time = time.time()
                

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

    print('done')





