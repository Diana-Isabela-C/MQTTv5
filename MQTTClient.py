import socket
import threading
from encoder import Encoder
from decoder import Decoder
import time


class MQTTClient:
    def __init__(self, client_id, lw_message):
        self.client_id = client_id
        self.username = ''
        self.password = ''
        self.lw_topic = 'test_topic'
        self.lw_message = lw_message
        self.socket = None
        self.encoder = Encoder()
        self.decoder = Decoder()
        self.connected = False
        self.last_ping = time.time()
        self.packet_id = 123
        # pachet id special pentru subscribe la chat

    def send_packet(self, packet):
        self.socket.send(packet)

    def receive_packet(self):
        CONNACK = 0x20
        PINGRESP = 0xD0
        PUBACK = 0x40
        PUBREC = 0x50
        PUBCOMP = 0x70
        SUBACK = 0x90

        while True:
            packet = self.socket.recv(1024)
            if not packet:
                break

            # CONNECT
            if packet[0] == CONNACK:
                if self.decoder.decode_connack(packet):
                    self.connected = True
                    print('Connection succesful')

            # PINGREQ
            if packet[0] == PINGRESP:
                print('Received PINGRESP')
                self.last_ping = time.time()
            if time.time() - self.last_ping > 5:
                time.sleep(1)
                print("PINGRESP not received within 5 seconds, closing connection")
                self.socket.close()

            # SUBSCRIBE
            if packet[0] == SUBACK:
                print('Received SUBACK')

            # PUBLISH
            # Qos 1
            if packet[0] == PUBACK:
                print('Received PUBACK')
            # QoS 2
            if packet[0] == PUBREC:
                print('Received PUBREC')
                # Send PUBREL
                self.send_packet(self.encoder.create_pubrel_packet(self.packet_id))
            if packet[0] == PUBCOMP:
                print('Received PUBCOMP')
                self.packet_id += 1



    def ping(self):
        # Trimit ping la fiecare 5 secunde
        while True:
            self.send_packet(self.encoder.create_pinreq_packet())
            self.last_ping = time.time()
            time.sleep(5)


    def start_client(self, broker_ip, broker_port):
        # Creaza un socket(IPv4, TCP) si conectare la broker
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((broker_ip, broker_port))

        # Thread pentru RECEIVE PACKET
        threading.Thread(target=self.receive_packet).start()


        # Trimit un packet CONNECT
        self.send_packet(self.encoder.create_connect_packet(self.client_id,
                                                            self.lw_topic, self.lw_message,
                                                            self.username, self.password))
        time.sleep(2)
        if self.connected:
            # Thread pentru PINGREQ
            threading.Thread(target=self.ping).start()

