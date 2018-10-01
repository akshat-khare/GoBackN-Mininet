import threading
import random
import time
import select
import socket

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

def add_zeroes_back(string, size):
    zeroes = '0' * (size-len(string))
    return string + zeroes

def get_lowest_ack(next_frame, ack):
    while next_frame%7 != ack:
        next_frame -= 1
    return next_frame

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
    length = int(msg[64:96], 2)
    r['info'] = msg[256:(256+length)]
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
    ack = (frame_expected + MAX_SEQ - 1) % MAX_SEQ
    sack = "{0:b}".format(ack)
    length = len(sinfo)
    slength = "{0:b}".format(length)
    # Construct the string to be sent. Done.
    # Todo -> Add checksum error bits
    msg = add_zeroes(sseq, 32) + add_zeroes(sack, 32) + add_zeroes(slength, 32) + add_zeroes('', 160) + sinfo
    msg = add_zeroes_back(msg, 2048)
    SOCKET.sendall(msg.encode('utf-8'))
    print ('--------------------------------')
    # print ('Sent the message with: frame:{0}\tack:{1}\n'.format(frame_nr, ack))
    print ('Sent message frame: {0} and ack: {1}, length: {2}'.format(frame_nr, ack, len(sinfo)))

def gobackn(socket, start_first, loss):
    global MAX_SEQ
    global SOCKET
    global LOSS
    global NETWORK_LAYER_READY
    global TIMEOUT

    LOSS = loss
    SOCKET = socket
    SOCKET.settimeout(2)
    SOCKET.setblocking(0)
    send_queue = []
    buffer = []

    next_frame_to_send = 0
    ack_expected = 0
    frame_expected = 0
    nbuffered = 0
    sender = start_first

    data_sent = True
    while True:
        frame_arrival = False
        ready_to_read, ready_to_write, error = select.select([SOCKET], [SOCKET], [SOCKET], 2)
        # print (ready_to_read, ready_to_write, error)
        if ready_to_read:
            print ('Socket is about to read. Waiting for data on socket.')
            # Receive message with some probability
            p = random.random()
            try:
                msg = SOCKET.recv(2048)
                if p > LOSS:
                    frame_arrival = True
                else:
                    data_sent = False
                    print ('PACKET NOT RECEIVED')
            except Exception:
                print ('Received timeout error.')

        if error:
            print ('Possible errors in socket')
            # Received timeout, re-send data
            if data_sent:
                print ('Time Up!')
                next_frame_to_send = get_lowest_ack(next_frame_to_send-1, ack_expected)
                for i in range(nbuffered):
                    send_data(next_frame_to_send, frame_expected, buffer)
                    next_frame_to_send = next_frame_to_send + 1

        if frame_arrival:
            r = parse_message(msg)
            print ('Received frame: {0} and ack: {1}, length: {2}'.format(r['seq'], r['ack'], len(r['info'])))
            if r['seq'] is frame_expected:
                print ('Received expected frame, with ack: {0}'.format(r['ack']))
                to_network_layer(r['info'])
                frame_expected = (frame_expected + 1) % MAX_SEQ
            print ('{0}\t{1}\t{2}'.format(ack_expected, r['ack'], next_frame_to_send))
            send_queue.append((frame_expected, next_frame_to_send, nbuffered))
            if between(ack_expected, r['ack'], next_frame_to_send):
                print ('Received expected ack')
                nbuffered = nbuffered - 1
                ack_expected = (ack_expected + 1) % MAX_SEQ
            
        send_frame = sender or frame_arrival
        # print (NETWORK_LAYER_READY)
        if send_queue or (NETWORK_LAYER_READY and send_frame):
            print ('Sending frame: {0}'.format(next_frame_to_send))
            buffer.append(from_network_layer())
            nbuffered = nbuffered + 1
            send_data(next_frame_to_send, frame_expected, buffer)
            data_sent = True
            next_frame_to_send = next_frame_to_send + 1 
            send_queue = send_queue[0:-1]
        
        if nbuffered < MAX_SEQ:
            NETWORK_LAYER_READY = True
        else:
            NETWORK_LAYER_READY = False

        if start_first:
            start_first = False
