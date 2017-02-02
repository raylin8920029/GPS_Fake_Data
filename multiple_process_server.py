import argparse
import SocketServer
import socket
import Queue
import time
import math
import gps_data_template
import multiprocessing
from multiprocessing.reduction import reduce_handle
from multiprocessing.reduction import rebuild_handle
from datetime import datetime


class MyTCPHandler(SocketServer.BaseRequestHandler):
    line_index = 0
    end_of_line = 0

    def handle(self):
        try:
            f = open(g_args.file_name)
            lines = f.readlines()
            self.end_of_line = len(lines) - 1
        except IOError:
            print 'cannot open', g_args.file_name
            raise

        h = reduce_handle(self.request.fileno())
        socket_queue.put(h)

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
        self.request.sendall(message)

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


class MultiprocessWorker(multiprocessing.Process):
    def __init__(self, sq):

        self.SLEEP_INTERVAL = 1

        # base class initialization
        multiprocessing.Process.__init__(self)

        # job management stuff
        self.socketQueue = sq
        self.kill_received = False

    def run(self):
        while not self.kill_received:
            try:
                #If you used pipe, then recieve as below
                #h=pipe.recv()
                #else dequeue

                h = self.socketQueue.get_nowait()
                fd=rebuild_handle(h)
                client_socket=socket.fromfd(fd,socket.AF_INET,socket.SOCK_STREAM)
                #client_socket.send("hellofromtheworkerprocess\r\n")
                received = client_socket.recv(1024)
                print "Recieved on client: ",received
                client_socket.close()

            except Queue.Empty:
                pass

            #Dummy timer
            time.sleep(self.SLEEP_INTERVAL)


def main():
    parser = argparse.ArgumentParser(description='Send message to client')
    parser.add_argument('srv_port', help='port of server')
    parser.add_argument('file_name', help='File name of the message')
    parser.add_argument('-r', "--repeat", default=-1, type=int,
                        help='Specify how many times you want to send the message, -1 means infinite')
    parser.add_argument('-i', "--interval", default=3, type=int,
                        help='Sets the interval between sending message, in seconds')

    global g_args
    g_args = parser.parse_args()

    # Create the server, binding to localhost
    server = SocketServer.TCPServer(('0.0.0.0', int(g_args.srv_port)), MyTCPHandler)
    global socket_queue
    socket_queue = multiprocessing.Queue()
    worker = []

    for i in range(2):
        worker.append(MultiprocessWorker(socket_queue))
        worker[i].start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
        server.server_close()

    for i in range(2):
        worker[i].join()


if __name__ == "__main__":
    main()
