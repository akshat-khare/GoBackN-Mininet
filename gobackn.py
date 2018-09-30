import threading

global SOCKET
global ADDR
MAX_SEQ = 7
NETWORK_LAYER_READY = True

def add_zeroes(string, size):
    zeroes = '0' * (size-len(string))
    return zeroes + string

def from_network_layer():
    # Todo -> Randomly generate data
    data = '0001000'
    return data

def to_network_layer(msg):
    # Todo -> Write this message onto a file
    print ('Received message: {0}', msg)

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
    r['info'] = msg[256:-32]
    r['ack'] = int(msg[32:64], 2)
    return r

def send_data(frame_nr, frame_expected, buffer):
    global ADDR
    sinfo = buffer[frame_nr]
    sseq = "{0:b}".format(frame_nr)
    sack = "{0:b}".format((frame_expected + MAX_SEQ) % (MAX_SEQ + 1))
    # Construct the string to be sent. Done.
    # Todo -> Add check sum error check
    msg = add_zeroes(sseq, 32) + add_zeroes(sack, 32) + add_zeroes('', 196) + sinfo
    SOCKET.sendto(msg, ADDR)
    # Start the timer thread

def gobackn(socket):
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
        msg, ADDR = SOCKET.recv(2048)
        if NETWORK_LAYER_READY:
            buffer[next_frame_to_send] = from_network_layer()
            nbuffered = nbuffered + 1
            send_data(next_frame_to_send, frame_expected, buffer)
            next_frame_to_send = next_frame_to_send + 1

        if msg is 'Frame Arrival':
            r = parse_message(msg)
            if r['seq'] is frame_expected:
                to_network_layer(r['info'])
                frame_expected = frame_expected + 1
            while between(ack_expected, r['ack'], next_frame_to_send):
                nbuffered = nbuffered - 1
                # Todo -> Stop the timer thread
                ack_expected = ack_expected + 1

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
