import threading
import random

global SOCKET
global ADDR
MAX_SEQ = 7
NETWORK_LAYER_READY = True

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
    print ('--------------------------------')
    print ('Received message.')

def between(a, b, c):
    abc = a<=b and b<c
    cab = c<a and a<=b
    bca = b<c and c<a
    if abc or cab or bca:
        return True
    return False

def parse_message(msg):
    # Parse the message and return a dictionary of seq_num, info and ack. Done.
    r = {}
    r['seq'] = int(msg[0:32], 2)
    r['ack'] = int(msg[32:64], 2)
    r['info'] = msg[256:-32]
    return r

def send_data(frame_nr, frame_expected, buffer):
    global ADDR
    sinfo = buffer[frame_nr]
    sseq = "{0:b}".format(frame_nr)
    # Ack of the received frame
    ack = (frame_expected + MAX_SEQ) % (MAX_SEQ + 1)
    sack = "{0:b}".format(ack)
    # Construct the string to be sent. Done.
    # Todo -> Add check sum error check
    msg = add_zeroes(sseq, 32) + add_zeroes(sack, 32) + add_zeroes('', 196) + sinfo
    SOCKET.sendall(msg.encode('utf-8'))
    print ('--------------------------------')
    print ('Sent the message with: frame:{0}\tack:{1}\n'.format(frame_nr, ack))
    # Start the timer thread

def gobackn(socket, start_first):
    global MAX_SEQ
    global SOCKET
    global ADDR
    global NETWORK_LAYER_READY

    SOCKET = socket
    buffer = []

    next_frame_to_send = 0
    ack_expected = 0
    frame_expected = 0
    nbuffered = 0

    while True:
        frame_arrival = False
        if not start_first:
            print ('Waiting for data on socket with details:')
            print ('frame: {0}\tack: {1}\tbuffer: {2}'.format(frame_expected, ack_expected, nbuffered))
            msg = SOCKET.recv(2048)
            frame_arrival = True
        else:
            start_first = False

        if frame_arrival:
            r = parse_message(msg)
            if r['seq'] is frame_expected:
                print ('Received expected frame, with ack: {0}'.format(r['ack']))
                to_network_layer(r['info'])
                frame_expected = frame_expected + 1
            while between(ack_expected, r['ack'], next_frame_to_send):
                nbuffered = nbuffered - 1
                # Todo -> Stop the timer thread
                ack_expected = ack_expected + 1
            
        if NETWORK_LAYER_READY:
            buffer.append(from_network_layer())
            nbuffered = nbuffered + 1
            send_data(next_frame_to_send, frame_expected, buffer)
            next_frame_to_send = next_frame_to_send + 1 

        timeout = False     # Todo -> Make a timer thread and check if timer has expired
        if timeout:
            next_frame_to_send = ack_expected
            for i in range(nbuffered):
                send_data(next_frame_to_send, frame_expected, buffer)
                next_frame_to_send = next_frame_to_send + 1
        
        if nbuffered < MAX_SEQ:
            NETWORK_LAYER_READY = True
        else:
            NETWORK_LAYER_READY = False
