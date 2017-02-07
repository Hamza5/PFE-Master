#!/usr/bin/env python3
DISTANCES_CAR_UUID = "ad6e04a5-2ae4-4c80-9140-34016e468ee7"

import bluetooth as bt

services = bt.find_service(uuid=DISTANCES_CAR_UUID)
if services:
    service = services[0]
    print('Service found !')
    print('Connecting to {} ({})...'.format(service['name'], service['host']))
    smartphone_socket = bt.BluetoothSocket()
    smartphone_socket.connect((service['host'], service['port']))
    smartphone_socket.setblocking(False)
    print('Connected !')
    while True:
        msg = input('> ')
        if msg :
            smartphone_socket.send(msg)
            try:
                print(str(smartphone_socket.recv(1024), encoding='utf-8', errors='ignore'))
            except bt.BluetoothError as err:
                print(err)
        else:
            break
    smartphone_socket.close();
    print('Connection closed !')
else:
    print('Service not found !')
