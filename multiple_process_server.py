import argparse
import SocketServer
import Queue
import time
import socket
import multiprocessing
import math
import gps_data_template
from datetime import datetime
from multiprocessing.reduction import reduce_handle
from multiprocessing.reduction import rebuild_handle


class MultiprocessWorker(multiprocessing.Process):
    def __init__(self, sq):
        self.SLEEP_INTERVAL = 1
        multiprocessing.Process.__init__(self)
        self.socket_queue = sq
        self.kill_received = False
        self.client_socket = None
        self.line_index = 0
        self.end_of_line = 0

    def run(self):
        while not self.kill_received:
            try:
                h = self.socket_queue.get_nowait()
                fd = rebuild_handle(h)
                self.client_socket = socket.fromfd(fd, socket.AF_INET, socket.SOCK_STREAM)

                f = open(g_args.file_name)
                lines = f.readlines()
                self.end_of_line = len(lines) - 1

                repeat = g_args.repeat

                if repeat <= -1:
                    while True:
                        self.send_message(lines, g_args.interval)
                        self.line_index += 1
                        if self.line_index > self.end_of_line:
                            self.line_index = 0
                else:
                    while repeat:
                        self.send_message(lines, g_args.interval)
                        self.line_index += 1
                        if self.line_index > self.end_of_line:
                            self.line_index = 0
                        repeat = repeat - 1

            except (Queue.Empty, KeyboardInterrupt):
                self.client_socket.close()

    def parse_file(self, lines):
        gprmc_time = datetime.utcnow().strftime("%H%M%S")
        gprmc_date = datetime.utcnow().strftime("%d%m%y")
        position_data = lines[self.line_index].split(',', 1)
        coordinate_latitude = float(position_data[0].rstrip())
        coordinate_longitude = float(position_data[1].rstrip())
        latitude_hemisphere = "S" if coordinate_latitude < 0 else "N"
        longitude_hemisphere = "W" if coordinate_longitude < 0 else "E"
        gprmc_latitude = self.dd_to_gprmc_dms_format(coordinate_latitude)
        if coordinate_latitude < 0:
            gprmc_latitude *= -1
        gprmc_longitude = self.dd_to_gprmc_dms_format(coordinate_longitude)
        if coordinate_longitude < 0:
            gprmc_longitude *= -1

        gprmc = gps_data_template.get_gps_data("GPRMC", Time=gprmc_time, Latitude=gprmc_latitude,
                                               Latitude_Hemisphere=latitude_hemisphere, Longitude=gprmc_longitude,
                                               Longitude_Hemisphere=longitude_hemisphere, Date=gprmc_date)

        msgList = []
        if gprmc.find('\r\n') < 0:
            msgList.append(gprmc + '\r\n')
        return msgList

    def send_message_to_client(self, message):
        print 'sending "%s"' % message
        self.client_socket.send(message)

    def send_message(self, lines, sleepIntv):
        msgList = self.parse_file(lines)
        for msg in msgList:
            self.send_message_to_client(msg)
            time.sleep(sleepIntv)

    def dd_to_gprmc_dms_format(self, degs):
        neg = degs < 0
        degs = (-1) ** neg * degs
        degs, d_int = math.modf(degs)
        mins, m_int = math.modf(60 * degs)
        secs = 60 * mins
        gprmc_dms_format = d_int * 100 + m_int + (secs / 100)
        return gprmc_dms_format


class MyTCPHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        h = reduce_handle(self.request.fileno())
        socket_queue.put(h)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Send message to client')
    parser.add_argument('srv_port', help='port of server')
    parser.add_argument('file_name', help='File name of the message')
    parser.add_argument('-r', "--repeat", default=-1, type=int,
                        help='Specify how many times you want to send the message, -1 means infinite')
    parser.add_argument('-i', "--interval", default=3, type=int,
                        help='Sets the interval between sending message, in seconds')

    g_args = parser.parse_args()

    HOST, PORT = "0.0.0.0", int(g_args.srv_port)
    server = SocketServer.TCPServer((HOST, PORT), MyTCPHandler)
    socket_queue = multiprocessing.Queue()

    for i in range(5):
        worker = MultiprocessWorker(socket_queue)
        worker.start()
