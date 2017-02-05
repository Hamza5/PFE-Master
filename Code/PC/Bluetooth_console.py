#!/usr/bin/env python3
DISTANCES_CAR_UUID = "ad6e04a5-2ae4-4c80-9140-34016e468ee7"

import bluetooth as bt

devices = bt.discover_devices(lookup_names=True)
print('Devices discovered :'.format(len(devices)))
for address, name in devices:
    print(address, name)
services = None
for mac_address, name in devices:
    services = bt.find_service(uuid=DISTANCES_CAR_UUID, address=mac_address)
    if services :
        print('Found the service in {}'.format(len(services), name))
        break
if services:
    service = services[0]
    print('Connecting to {}:{}...'.format(service['host'], service['port']))
    smartphone_socket = bt.BluetoothSocket()
    smartphone_socket.connect((service['host'], service['port']))
    smartphone_socket.setblocking(True)
    print('Connected !')
    while True:
        # msg = input('> ')
        # if msg :
            # smartphone_socket.send(msg)
            try:
                print(smartphone_socket.recv(1024).decode(encoding='utf-8'))
            except bt.BluetoothError as err:
                print(err)
                break
        # else:
            # break
    smartphone_socket.close();
    print('Connection closed !')
