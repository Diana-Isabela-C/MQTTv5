class Encoder:
    # CONNECT -> Flags (8 biti)
    # |        b7|        b6|           b5|      b4|       b3|         b2|           b1|     b0 |
    # | username | password | will retain |     will QoS     | will flag | clean start | retain |
    # dup - duplicate message (pentru publicare cu qos 1 sau 2)
    # qos 0 -> 00
    # qos 1 -> 01
    # qos 2 -> 10
    def create_connect_packet(self, client_id, lw_topic, lw_message, username, password) -> bytearray:
        # -------------------- FIXED HEADER -----------------------#
        packet = bytearray()
        packet.extend(b'\x10')                      # CONNECT = 1, flag = 0
        packet.extend(b'\x00')                      # placeholder pentru lungimea ramasa
        # ------------------- VARIABLE HEADER ---------------------#
        packet.extend(b'\x00\x04MQTT\x05\xC6')      # name length(2 octeti)\protocol MQTT\v5\flags
        packet.extend(b'\x00\x05')                  # Keepalive  (2 octeti)
        # ----------------------- PAYLOAD -------------------------#
        # Lungimea proprietatilor intervalului de expirare (adica 0)
        packet.extend(b'\x00')

        # ID client
        packet.extend((len(client_id)).to_bytes(2, 'big'))         # Client ID length
        packet.extend(client_id.encode(errors='replace'))          # Client ID ('replace' -> '?')

        # Last Will parameters
        packet.extend(b'\x00')                  # Will properties length (FARA PROPRIETATI)
        packet.extend((len(lw_topic)).to_bytes(2, 'big'))          # Last Will Topic length
        packet.extend(lw_topic.encode(errors='replace'))           # Last Will Topic
        packet.extend((len(lw_message)).to_bytes(2, 'big'))        # Last Will Message length
        packet.extend(lw_message.encode(errors='replace'))         # Last Will Message

        # Username & password
        packet.extend((len(username)).to_bytes(2, 'big'))          # Username length
        packet.extend(username.encode('utf-8', errors='replace'))  # Username
        packet.extend((len(password)).to_bytes(2, 'big'))          # Password length
        packet.extend(password.encode('utf-8', errors='replace'))  # Password

        # Setez octetii pentru campul lungime ramasa
        packet[1:2] = (len(packet) - 2).to_bytes(1, 'big')

        return packet


    def create_pinreq_packet(self):
        return bytearray(b'\xC0\00')


    def create_disconnect_packet(self):
        # DISCONNECT = 0xE0
        return bytearray(b'\xE0\x00')

    # PUBLISH -> Flags (ultimii 4 biti - cei mai nesemnificativi)
    # |   b3|    b2|   b1|     b0|
    # |  DUP|     qos    | retain|
    # dup - duplicate message (pentru publicare cu qos 1 sau 2)
    # qos 0 -> 00
    # qos 1 -> 01
    # qos 2 -> 10
    def create_publish_packet(self, packet_id, qos, topic, message):
        # --------------------- FIXED HEADER -----------------------#
        packet = bytearray()
        if qos == 0:
            packet.extend(b'\x30')  # PUBLISH = 3, QoS flag = 0
        elif qos == 1:
            packet.extend(b'\x32')  # PUBLISH = 3, QoS flag = 1
        elif qos == 2:
            packet.extend(b'\x34')  # PUBLISH = 3, QoS flag = 2
        else:
            raise ValueError("Nivel QoS invalid. Trebuie sa fie 0, 1 sau 2.")
        packet.extend(b'\x00')  # placeholder pentru lungimea ramasa
        # -------------------- VARIABLE HEADER ---------------------#
        packet.extend((len(topic)).to_bytes(2, 'big'))  # Topic length
        packet.extend(topic.encode('utf-8'))            # Topic
        # pentru qos>0 e necesar packet ID
        if qos > 0:
            packet.extend(packet_id.to_bytes(2, 'big'))
        packet.extend(b'\x00')                  # Properties length
        packet.extend(message.encode('utf-8'))  # Message payload

        # Setez octetii pentru campul lungime ramasa
        packet[1:2] = (len(packet) - 2).to_bytes(1, 'big')

        return packet

    def create_pubrel_packet(self, packet_id):
        # Pubrel id + remaining length
        packet = bytearray(b'\x62\x02')
        packet += packet_id.to_bytes(2, 'big')

        return packet

    def create_subscribe_packet(self, packet_id, topic, qos):
        # --------------------- FIXED HEADER -----------------------#
        packet = bytearray()
        if qos not in [0, 1, 2]:
            raise ValueError("Nivel QoS invalid. Trebuie sa fie 0, 1 sau 2.")
        packet.extend(b'\x82')               # SUBSCRIBE = 8, flags = 2
        packet.extend(b'\x00')               # placeholder pentru lungimea ramasa
        # -------------------- VARIABLE HEADER ---------------------#
        packet.extend(packet_id.to_bytes(2, 'big'))     # Packet ID
        packet.extend(b'\x00')                          # Property length
        # ------------------------ PAYLOAD -------------------------#
        packet.extend((len(topic)).to_bytes(2, 'big'))  # Topic length
        packet.extend(topic.encode('utf-8'))            # Topic
        packet.extend(qos.to_bytes(1, 'big'))           # QoS level

        # Setez octetii pentru campul lungime ramasa
        packet[1:2] = (len(packet) - 2).to_bytes(1, 'big')

        return packet
