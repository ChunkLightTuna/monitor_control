import socket
import threading
from threading import Event

import numpy
import sounddevice as sd
from sounddevice import CallbackFlags

assert numpy
host_name = socket.gethostname()
host_ip = socket.gethostbyname(host_name)
print(host_ip)
port = 50001


def audio_stream_udp():
    buff_size = 65536
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, buff_size)
    print('starting server')
    server_socket.bind((host_ip, port))
    print('waiting for client conection')
    msg, client_addr = server_socket.recvfrom(buff_size)
    print('GOT connection from ', client_addr, msg)

    # def callback(in_data, out_data, frames, time, status):
    #     out_data[:] = in_data
    #     print(len(in_data))
    #
    # def out_cal(outdata, frames: int, time, status: CallbackFlags) -> None:
    #
    #     print('ok?')

    # output_stream = sd.RawOutputStream(channels=1)

    def in_cal(indata, frames: int, time, status: CallbackFlags) -> None:
        print('sending')
        print(indata)
        server_socket.sendto(indata, client_addr)
        print('sent')
        # output_stream.write(indata)

    # stream = sd.RawStream(callback=callback, channels=1)
    input_stream = sd.RawInputStream(callback=in_cal, channels=1)
    # stream.start()
    # output_stream.start()
    input_stream.start()

    # sd.wait()
    Event().wait()


t1 = threading.Thread(target=audio_stream_udp, args=())
t1.start()
