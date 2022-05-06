import queue
import socket
import threading
from time import sleep

import sounddevice as sd

host_name = socket.gethostname()
host_ip = socket.gethostbyname(host_name)
print(host_ip)
port = 50001
q = queue.Queue(maxsize=2000)


def audio_stream_udp():
    BUFF_SIZE = 65536
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)

    def callback(in_data, out_data, frames, time, status):
        out_data[:] = q.get()

    # create socket
    message = b'Hello from client!'
    client_socket.sendto(message, (host_ip, port))

    def get_audio_data():
        while True:
            frame, _ = client_socket.recvfrom(BUFF_SIZE)
            q.put(frame)
            print('Queue size...', q.qsize())

    t1 = threading.Thread(target=get_audio_data, args=())
    t1.start()
    sleep(5)
    print('Now Playing...')

    stream = sd.Stream(callback=callback)
    stream.start()


t1 = threading.Thread(target=audio_stream_udp, args=())
t1.start()
