import tkinter.scrolledtext
from tkinter import *
from tkinter import ttk
from MQTTClient import *
import wmi
import shutil


BROKER_IP_ADDRESS = '172.20.10.4'  # incearca 'localhost' pentru mosquitto
BROKER_IP_ADDRESS_SUNA = '192.168.100.43'
ip_edurom = '192.168.58.143'
loopback = '127.0.0.1'

BROKER_PORT = 1883  # Port special pentru MQTT
USERNAME = 'student'
PASSWORD = 'retele'
TOPIC = 'test topic'
LASTWILL_TOPIC = 'last/will'  # poate nu trb neaparat inclus?

# Packet types (primii 4 biti - cei mai semnificativi)
CONNECT = 1
PUBLISH = 3
SUBSCRIBE = 8
DISCONNECT = 14




def login():
    if entry_clientID.get() == '' or entry_address.get() == '':
        from tkinter import messagebox
        messagebox.showwarning(title='Invalid creditentials',
                               message='Please enter a client ID and a broker address.')
        return False

    if entry_username.get() == '' or entry_password.get() == '':
        from tkinter import messagebox
        messagebox.showwarning(title='Invalid creditentials',
                               message='Please enter a username and a password.')
        return False

    mqtt_client.username = entry_username.get()
    mqtt_client.password = entry_password.get()

    mqtt_client.start_client(entry_address.get(), BROKER_PORT)

    subscriptions_menu["state"] = NORMAL
    topic_menu_publish["state"] = NORMAL
    subscribe_button["state"] = NORMAL
    publish_button['state'] = NORMAL


subscriptions_list = []


def subscribe(packet_id, topic):
    text_box_subscriptions.delete('1.0', tkinter.END)
    qos = 0
    match topic:
        # Topic cu QoS 2
        case 'Chat':
            if 'Chat' not in subscriptions_list:
                subscriptions_list.append('Chat')
            entry_publish['state'] = NORMAL
            qos = 2
        case 'CPU temp':
            if 'CPU temp' not in subscriptions_list:
                subscriptions_list.append('CPU temp')
            qos = 1
        case 'Disk usage':
            if 'Disk usage' not in subscriptions_list:
                subscriptions_list.append('Disk usage')
            qos = 0

    # Trimitere pachet subscribe
    mqtt_client.send_packet(mqtt_client.encoder.create_subscribe_packet(packet_id, topic, qos))

    # Actualizare text box
    for item in subscriptions_list:
        text_box_subscriptions.insert(tkinter.END, item)
        text_box_subscriptions.insert(tkinter.END, '\n')

    # Actualizez drop down-ul pentru optiuni de publish
    topic_menu_publish.config(values=subscriptions_list)



chat_list = []


def publish(packet_id, topic, msg):
    text_box_clients.delete('1.0', tkinter.END)
    # Aleg un packet id nou
    mqtt_client.packet_id += 1
    match topic:
        case 'Chat':
            client_msg = f'{entry_clientID.get()}: {msg}\n'
            qos = 2
            mqtt_client.send_packet(mqtt_client.encoder.create_publish_packet(packet_id, qos, topic, client_msg))
            chat_list.append(client_msg)
            for item in chat_list:
                text_box_clients.insert(tkinter.END, item)

        case 'CPU temp':
            qos = 1
            text_box_clients.insert(tkinter.END, f'{mqtt_client.client_id}:\n')

            # Functii pentru a afla temperatura procesorului
            #TODO
            # RULEAZA OPEN HARDWARE MONITOR PE FUNDAL CA SA MEARGA FUNCTIA DE MAI JOS
            w = wmi.WMI(namespace="root\\OpenHardwareMonitor")
            temperature_infos = w.Sensor()
            for sensor in temperature_infos:
                if sensor.SensorType == u'Temperature':
                    cpu_temp = f'{sensor.Name}: {sensor.Value} C\n'
                    mqtt_client.send_packet(mqtt_client.encoder.create_publish_packet(
                        packet_id, qos, topic, cpu_temp)
                    )
                    text_box_clients.insert(tkinter.END, cpu_temp)

        case 'Disk usage':
            qos = 0
            stat = shutil.disk_usage("/")

            # Calculul spatiului de stocare folosit
            msg = (f'{mqtt_client.client_id}:\n' +
                   'Total: %d GiB' % (stat.total // (2 ** 30)) +
                   '\nUsed: %d GiB' % (stat.used // (2 ** 30)) +
                   '\nFree: %d GiB' % (stat.free // (2 ** 30)))
            mqtt_client.send_packet(mqtt_client.encoder.create_publish_packet(packet_id, qos, topic, msg))
            text_box_clients.insert(tkinter.END, msg)
    entry_publish.delete(0, END)

def switch_to_chat():
    topic_menu_publish.set('Chat')
    text_box_clients.delete('1.0', tkinter.END)
    for item in chat_list:
        text_box_clients.insert(tkinter.END, item)


def logout():
    try:
        mqtt_client.send_packet(mqtt_client.encoder.create_disconnect_packet())
        data = mqtt_client.socket.recv(1024)
        print('Received last will message: {!r}'.format(data))
    finally:
        print('Closing socket')
        mqtt_client.socket.close()


#------------------------------- UI SETUP  -----------------------------------#
YELLOW = "#f7f5dd"


# Window
window = Tk()
window.title("MQTTv5 Client")
window.config(padx=50, pady=50, bg=YELLOW)

# Logo
mqtt_img = PhotoImage(file="mqtt_logo.png")
canvas = Canvas(width=287, height=100, bg=YELLOW, highlightthickness=0)
canvas.create_image(143, 37, image=mqtt_img)
canvas.grid(row=0, column=0, columnspan=5)

# Text boxes
text_box_clients = tkinter.scrolledtext.ScrolledText(width=50, height=25)
text_box_clients.grid(row=1, column=0, rowspan=64)


text_box_subscriptions = tkinter.scrolledtext.ScrolledText(width=45, height=9)
text_box_subscriptions.grid(row=13, column=1, columnspan=4)


# Frames
frame_login = LabelFrame(window, text="Login", bg=YELLOW)
frame_login.grid(row=1, column=1, padx=10, pady=5, columnspan=4)

frame_actions = LabelFrame(window, text="Actions", bg=YELLOW)
frame_actions.grid(row=10, column=1, padx=10, pady=5, columnspan=4)

# Labels
Label(frame_login, text="Client ID:", bg=YELLOW).grid(row=1, column=1)
Label(frame_login, text="Broker address:", bg=YELLOW).grid(row=2, column=1, padx=10)
Label(frame_login, text="Username:", bg=YELLOW).grid(row=1, column=3)
Label(frame_login, text="Password:", bg=YELLOW).grid(row=2, column=3)
Label(frame_actions, text="Choose topic:", bg=YELLOW).grid(row=10, column=1, padx=10)
Label(frame_actions, text="Publish to topic:", bg=YELLOW).grid(row=11, column=1, padx=10)
Label(frame_actions, text="Subscriptions:", bg=YELLOW).grid(row=12, column=1, padx=10)

Label(window, text="Clients", bg=YELLOW, font=('Courier', 15, 'bold')).grid(row=65, column=0)
Label(window, text="Subscriptions", bg=YELLOW, font=('Courier', 15, 'bold')).grid(row=65, column=2, columnspan=11)

# Text entry
entry_clientID = Entry(frame_login)
entry_clientID.insert(0, 'client-1')
entry_address = Entry(frame_login)
entry_address.insert(0, loopback)
entry_username = Entry(frame_login)
entry_password = Entry(frame_login, show="*")
entry_publish = Entry(frame_actions, width=41)
entry_publish['state'] = DISABLED

entry_clientID.grid(row=1, column=2)
entry_address.grid(row=2, column=2)
entry_username.grid(row=1, column=4, pady=5)
entry_password.grid(row=2, column=4, pady=5)
entry_publish.grid(row=11, column=2, columnspan=2)

# Drop menu
topic_list_subscribe = ['Chat', 'CPU temp', 'Disk usage']
subscriptions_menu = ttk.Combobox(frame_actions, values=topic_list_subscribe, width=17)
subscriptions_menu.grid(row=10, column=2, pady=5)
subscriptions_menu["state"] = DISABLED

topic_menu_publish = ttk.Combobox(frame_actions, values=subscriptions_list, width=17)
topic_menu_publish.grid(row=12, column=2, pady=5)
topic_menu_publish["state"] = DISABLED

# Buttons
Button(frame_login, text="Login", width=17, command=login).grid(row=4, column=4, padx=10, pady=10, columnspan=3)
subscribe_button = Button(frame_actions, text="Subscribe", width=16, command=lambda: subscribe(mqtt_client.packet_id,
                                                                                               subscriptions_menu.get()))
subscribe_button.grid(row=10, column=3, padx=10, pady=10)
subscribe_button['state'] = DISABLED

Button(window, text="Chat", width=17, command=switch_to_chat).grid(row=66, column=0)
Button(window, text="Logout", width=17, command=logout).grid(row=66, column=3)
publish_button = Button(frame_actions, text="Publish", width=16, command=lambda: publish(mqtt_client.packet_id,
                                                                                         topic_menu_publish.get(),
                                                                                         entry_publish.get()))
publish_button.grid(row=12, column=3, pady=5)
publish_button['state'] = DISABLED

for widget in frame_login.winfo_children():
    widget.grid_configure(padx=5, pady=5)

for widget in frame_actions.winfo_children():
    widget.grid_configure(padx=5, pady=5)

#----------------------------------- MAIN ------------------------------------#

CLIENT_ID = entry_clientID.get()
LASTWILL_MESSAGE = f'{USERNAME} has lost connection to the server.'

mqtt_client = MQTTClient(CLIENT_ID, LASTWILL_MESSAGE)

# Start interfata
window.mainloop()


# TODO 2: Monitorizarea unor parametri (ex: temperatura cpu) si
#  publicarea lor periodica pe topicuri dedicate + afisarea parametrilor
#  monitorizati de alte instante ale aplicatiei (local sau pe alte masini)

# TODO 3: Autentificare cu user si parola

