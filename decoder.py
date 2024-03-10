class Decoder:
    def decode_connack(self, packet):
        CONNACK = 0x20
        if packet[0] == CONNACK:
            print('Received CONNACK')

        if packet[3] == 0:  # 0 -> conexiune reusita
            return True
        else:
            return False

