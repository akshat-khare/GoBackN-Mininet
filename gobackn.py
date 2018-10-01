import threading
import random
import time
import socket

LOCK = threading.Lock()
TIMEOUT = 2
TIMEUP = False
NETWORK_LAYER_READY = False

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

next_frame_to_send = 0
ack_expected = 0
frame_expected = 0
nbuffered = 0

def recv_data():
    global next_frame_to_send
    global ack_expected
    global frame_expected
    global nbuffered

    while True:
        try:
            msg = SOCKET.recv(2048)
            print ('Received message from socket: {0}'.format(msg))
            p = random.random()
            if p > LOSS:
                LOCK.acquire()
                
                r = parse_message(msg)
                if r['seq'] is frame_expected:
                    print ('Received expected frame, with ack: {0}'.format(r['ack']))
                    to_network_layer(r['info'])
                    frame_expected = (frame_expected + 1) % MAX_SEQ
                    ACK_READY = True
                    print ('Ack ready set to true')
                if between(ack_expected, r['ack'], next_frame_to_send):
                    nbuffered = nbuffered - 1
                    ack_expected = (ack_expected + 1) % MAX_SEQ

                LOCK.release()
        except socket.timeout:
            LOCK.acquire()
            print ('Received Timeout Error')
            TIMEUP = True
            LOCK.release()

def gobackn(socket, max_seq, start_first, loss):
    global next_frame_to_send
    global ack_expected
    global frame_expected
    global nbuffered

    global NETWORK_LAYER_READY
    global SOCKET
    global MAX_SEQ
    global TIMEUP
    global LOSS
    global ACK_READY

    LOSS = loss
    MAX_SEQ = max_seq
    ACK_READY = False
    SOCKET = socket
    SOCKET.settimeout(2)
    SOCKET.setblocking(0)
    buffer = []

    data_sent = True
    recv_thread = threading.Thread(target=recv_data)
    recv_thread.start()

    while True:
        if TIMEUP:
            # Received timeout, re-send data
            if data_sent:
                LOCK.acquire()
                print ('Time Up!')
                next_frame_to_send = get_lowest_ack(next_frame_to_send-1, ack_expected)
                for i in range(nbuffered):
                    send_data(next_frame_to_send, frame_expected, buffer)
                    next_frame_to_send = next_frame_to_send + 1
                LOCK.release()
            
        # print (NETWORK_LAYER_READY)
        if NETWORK_LAYER_READY or start_first:
            print ('Sending frame: {0}'.format(next_frame_to_send))
            buffer.append(from_network_layer())
            LOCK.acquire()
            print ('Sending message.')
            nbuffered = nbuffered + 1
            data_sent = True
            ACK_READY = False
            next_frame_to_send = next_frame_to_send + 1
            LOCK.release() 
            send_data(next_frame_to_send-1, frame_expected, buffer)
        
        if nbuffered < MAX_SEQ:
            NETWORK_LAYER_READY = True
        else:
            NETWORK_LAYER_READY = False

        if start_first:
            start_first = False