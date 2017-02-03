import os
import io
import sys
import socket
import multiprocessing as mp
from time import sleep

DEGREE_OF_PARALLELISM = 4
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 3333


def _parse_cmd_line_args():
    arguments = sys.argv
    if len(arguments) == 1:
        return DEFAULT_HOST, DEFAULT_PORT
    raise NotImplementedError


def debug(data):
    filename = 'log{}.txt'.format(os.getpid())
    with open(filename, mode='a', encoding='utf8') as file:
        file.write(str(data) + '\n')


def handle_connection(client):
    client_data = client.recv(1024)
    debug('received data from client: ' + str(len(client_data)))
    response = client_data.upper()
    client.send(response)
    debug('sent data from client: ' + str(response))


def listen(server_socket):
    debug('started listen function')

    pid = os.getpid()

    while True:
        debug('Sub process {0} is waiting for connection...'.format(str(pid)))

        client, address = server_socket.accept()
        debug('Sub process {0} accepted connection {1}'.format(
            str(pid), str(client)))

        handle_connection(client)
        client.close()
        debug('Sub process {0} finished handling connection {1}'.format(
            str(pid), str(client)))


if __name__ == "__main__":
    host_port = _parse_cmd_line_args()
    print('Server is running...')
    print('Degree of parallelism: ' + str(DEGREE_OF_PARALLELISM))

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print('Socket created.')
    host, port = "0.0.0.0", 1245
    server_socket.bind((host, port))
    server_socket.listen(DEGREE_OF_PARALLELISM)
    print('Socket bount to: ' + str(port))

    children = []
    for i in range(DEGREE_OF_PARALLELISM):
        child_process = mp.Process(target=listen, args=(server_socket,))
        child_process.daemon = True
        child_process.start()
        children.append(child_process)

        while not child_process.pid:
            sleep(.25)

        print('Process {0} is alive: {1}'.format(str(child_process.pid),
                                                 str(child_process.is_alive())))
    print()

    kids_are_alive = True
    while kids_are_alive:
        print('Press ctrl+c to kill all processes.\n')
        sleep(1)

        exit_codes = []
        for child_process in children:
            print('Process {0} is alive: {1}'.format(str(child_process.pid),
                                                     str(child_process.is_alive())))
            print('Process {0} exit code: {1}'.format(str(child_process.pid),
                                                      str(child_process.exitcode)))
            exit_codes.append(child_process.exitcode)

        if all(exit_codes):
            kids_are_alive = False