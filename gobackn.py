import threading
import random
import time

global SOCKET
global ADDR
global LOSS

TIMEOUT = 2
MAX_SEQ = 7
NETWORK_LAYER_READY = True

current_milli_time = lambda: int(round(time.time() * 1000))

def add_zeroes(string, size):
    zeroes = '0' * (size-len(string))
    return zeroes + string

def from_network_layer():
    # Randomly generate data. Done.
    repeat_string = random.randint(0, 65535)
    times = random.randint(16, 110)
    data = add_zeroes(bin(repeat_string)[2:], 16) * times
    return data

def to_network_layer(msg):
    # Todo -> Write this message onto a file
    print ('Received message.')

def parse_message(msg):
    # Parse the message and return a dictionary of seq_num, info and ack. Done.
    r = {}
    r['seq'] = int(msg[0:32], 2) % MAX_SEQ
    r['ack'] = int(msg[32:64], 2)
    r['info'] = msg[256:-32]
    return r

def between(a, b, c):
    abc = a<=b and b<c
    cab = c<a and a<=b
    bca = b<c and c<a
    if abc or cab or bca:
        return True
    return False

def send_data(frame_nr, frame_expected, buffer):
    global LOSS
    sinfo = buffer[frame_nr]
    sseq = "{0:b}".format(frame_nr)
    # Ack of the received frame
    ack = (frame_expected + MAX_SEQ - 1) % MAX_SEQ
    sack = "{0:b}".format(ack)
    # Construct the string to be sent. Done.
    # Todo -> Add checksum error bits
    msg = add_zeroes(sseq, 32) + add_zeroes(sack, 32) + add_zeroes('', 196) + sinfo
    SOCKET.sendall(msg.encode('utf-8'))
    print ('--------------------------------')
    print ('Sent the message with: frame:{0}\tack:{1}\n'.format(frame_nr, ack))

def gobackn(socket, start_first, loss):
    global MAX_SEQ
    global SOCKET
    global LOSS
    global NETWORK_LAYER_READY

    LOSS = loss
    SOCKET = socket
    SOCKET.settimeout(TIMEOUT)
    buffer = []

    next_frame_to_send = 0
    ack_expected = 0
    frame_expected = 0
    nbuffered = 0

    data_sent = True
    while True:
        frame_arrival = False
        if not start_first:
            print ('Waiting for data on socket.')
            # Receive message with some probability
            p = random.random()
            try:
                msg = SOCKET.recv(2048)
                if p > LOSS:
                    frame_arrival = True
                else:
                    data_sent = False
                    print ('PACKET NOT RECEIVED')
            except Exception as e:
                # Received timeout, re-send data
                if data_sent:
                    print ('Time Up!')
                    next_frame_to_send = ack_expected
                    for i in range(nbuffered):
                        send_data(next_frame_to_send, frame_expected, buffer)
                        next_frame_to_send = next_frame_to_send + 1

        if frame_arrival:
            r = parse_message(msg)
            if r['seq'] is frame_expected:
                print ('Received expected frame, with ack: {0}'.format(r['ack']))
                to_network_layer(r['info'])
                frame_expected = (frame_expected + 1) % MAX_SEQ

            if between(ack_expected, r['ack'], next_frame_to_send):
                nbuffered = nbuffered - 1
                ack_expected = (ack_expected + 1) % MAX_SEQ
            
        send_frame = start_first or frame_arrival
        if NETWORK_LAYER_READY and send_frame:
            buffer.append(from_network_layer())
            nbuffered = nbuffered + 1
            send_data(next_frame_to_send, frame_expected, buffer)
            data_sent = True
            next_frame_to_send = next_frame_to_send + 1 
        
        if nbuffered < MAX_SEQ:
            NETWORK_LAYER_READY = True
        else:
            NETWORK_LAYER_READY = False

        if start_first:
            start_first = False
