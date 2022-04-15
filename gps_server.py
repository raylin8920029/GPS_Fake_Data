import argparse
import time
import math
import threading
import SocketServer
import gps_data_template
from datetime import datetime


g_args = None
gps_status = 'A'
gps_speed = 30


class MyTCPHandler(SocketServer.BaseRequestHandler):
    line_index = 0
    end_of_line = 0

    def handle(self):
        # coordinate data
        coordinate_lines = ""

        try:
            coordinate_file = open(g_args.file_name)
            coordinate_lines = coordinate_file.readlines()
            self.end_of_line = len(coordinate_lines) - 1
        except IOError:
            print ('cannot open', g_args.file_name)

        repeat = g_args.repeat
        while repeat != 0:
            if not self.send_message(coordinate_lines, g_args.interval):
                break

            self.line_index += 1
            if self.line_index > self.end_of_line:
                self.line_index = 0

            if repeat > 0:
                repeat -= 1

    def parse_file(self, lines):
        gprmc_time = datetime.utcnow().strftime("%H%M%S")
        gprmc_date = datetime.utcnow().strftime("%d%m%y")
        position_data = lines[self.line_index].split(',', 1)
        coordinate_latitude = float(position_data[0].rstrip())
        coordinate_longitude = float(position_data[1].rstrip())
        latitude_hemisphere = "S" if coordinate_latitude < 0 else "N"
        longitude_hemisphere = "W" if coordinate_longitude < 0 else "E"
        gprmc_latitude = self.dd_to_gprmc_dmm_format(coordinate_latitude)
        gprmc_longitude = self.dd_to_gprmc_dmm_format(coordinate_longitude)

        gprmc = gps_data_template.get_gps_data("GPRMC", Time=gprmc_time, Status=gps_status, Latitude=gprmc_latitude, Latitude_Hemisphere=latitude_hemisphere, Longitude=gprmc_longitude, Longitude_Hemisphere=longitude_hemisphere, Date=gprmc_date, Speed=gps_speed)

        msg_list = []
        if gprmc.find('\r\n') < 0:
            msg_list.append(gprmc + '\r\n')
        return msg_list

    def send_message_to_client(self, message):
        print ('%s sending "%s"' % (self.client_address, message))
        self.request.sendall(message)

    def send_message(self, lines, sleep_interval):
        msg_list = self.parse_file(lines)
        for msg in msg_list:
            try:
                self.send_message_to_client(msg)
            except Exception as detail:
                print ('%s Send message error! %s' % (self.client_address, detail))
                return False

        time.sleep(sleep_interval)
        return True

    def dd_to_gprmc_dmm_format(self, degrees):
        # dd (decimal degrees) to dms (degrees minutes seconds)
        dd_degrees = math.fabs(degrees)
        dms_degrees_fractional, dms_degrees_integer = math.modf(dd_degrees)
        dms_minutes_fractional, dms_minutes_integer = math.modf((dd_degrees - dms_degrees_integer) * 60)
        dms_secondes = (dd_degrees-dms_degrees_integer - dms_minutes_integer / 60) * 3600
        # dms (degrees minutes seconds) to dmm (degrees and decimal minutes)
        gprmc_dmm_format = dms_degrees_integer * 100 + dms_minutes_integer + (dms_secondes / 60)
        return round(gprmc_dmm_format, 4)

def key_control():
    def getch():
        import platform

        if platform.system() == 'Windows':
            import msvcrt
            return msvcrt.getche()
        else:
            import termios, tty
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch

    global gps_status, gps_speed

    while True:
        ctrl_key = getch()
        if ctrl_key == 'a':
            print ('GPS status is valid')
            gps_status = 'A'
        elif ctrl_key == 'v':
            print ('GPS status is invalid')
            gps_status = 'V'
        elif ctrl_key == '+':
            gps_speed = gps_speed if gps_speed >= 200 else gps_speed + 5
            print ('GPS speed [+]:%d(knod), %f(kph), %f(mph)' % \
                (gps_speed, gps_speed * 1.85200, gps_speed * 1.15077945))
        elif ctrl_key == '-':
            gps_speed = gps_speed if gps_speed <= 0 else gps_speed - 5
            print ('GPS speed [-]:%d(knod), %f(kph), %f(mph)' % \
                (gps_speed, gps_speed * 1.85200, gps_speed * 1.15077945))
        elif ctrl_key == 'q':
            break

def main():
    parser = argparse.ArgumentParser(description='Send message to client')
    parser.add_argument('srv_port', help='port of server')
    parser.add_argument('file_name', help='File name of the message')
    parser.add_argument('-r', "--repeat", default=-1, type=int, help='Specify how many times you want to send the message, -1 means infinite')
    parser.add_argument('-i', "--interval", default=3, type=int, help='Set the interval for sending message, in seconds')

    server = None

    global g_args
    g_args = parser.parse_args()

    threading.Thread(target=key_control, args=(), name='key_control').start()

    try:
        SocketServer.ThreadingTCPServer.allow_reuse_address = True
        SocketServer.ThreadingTCPServer.daemon_threads = True
        # Create gps server, binding to localhost
        server = SocketServer.ThreadingTCPServer(("0.0.0.0", int(g_args.srv_port)), MyTCPHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        if type(server) is SocketServer:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    main()
