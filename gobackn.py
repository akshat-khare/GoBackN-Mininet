import threading
import random
import time
import socket

LOCK = threading.Lock()
TIMEOUT = 1000
TIMEUP = False
ACK_READY = False
NETWORK_LAYER_READY = True

BASE_TIME = int(round(time.time() * 1000))
current_milli_time = lambda: int(round(time.time() * 1000) - BASE_TIME)
TIMER = current_milli_time()

def add_zeroes(string, size):
    zeroes = '0' * (size-len(string))
    return zeroes + string

def add_zeroes_back(string, size):
    zeroes = '0' * (size-len(string))
    return string + zeroes

def get_lowest_ack(next_frame, ack):
    print ()
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
    # print ('R: Received message.')
    pass

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

def sent_details(frame, ack, length):
    global TIMER
    print ('\tSent Message: {0} of length: {1} and ack: {2} at time: {3}'.format(frame, length, ack, TIMER))

def send_data(frame_nr, frame_expected, buffer):
    sinfo = buffer[frame_nr]
    sseq = "{0:b}".format(frame_nr)
    ack = (frame_expected + MAX_SEQ - 1) % MAX_SEQ
    sack = "{0:b}".format(ack)
    length = len(sinfo)
    slength = "{0:b}".format(length)
    # Construct the string to be sent. Done.
    msg = add_zeroes(sseq, 32) + add_zeroes(sack, 32) + add_zeroes(slength, 32) + add_zeroes('', 160) + sinfo
    msg = add_zeroes_back(msg, 2048)
    SOCKET.sendall(msg.encode('utf-8'))
    print ('--------------------------------')
    sent_details(frame_nr, ack, len(sinfo))
    # print ('S: Sent message frame: {0} and ack: {1}, length: {2}'.format(frame_nr, ack, len(sinfo)))

next_frame_to_send = 0
ack_expected = 0
frame_expected = 0
nbuffered = 0
data_sent = True

def recieved_details(parsed_msg):
    global frame_expected
    global ack_expected
    print ('\tExpected frame: {0} and ack: {1}'.format(frame_expected, ack_expected))
    print ('\tReceived frame: {0} of length: {1} and ack: {2}'.format(parsed_msg['seq'], len(parsed_msg['info']), parsed_msg['ack']))

def recv_data():
    global next_frame_to_send
    global ack_expected
    global frame_expected
    global nbuffered
    global data_sent

    global ACK_READY
    global TIMER

    while True:
        try:
            SOCKET.settimeout(10)
            msg = SOCKET.recv(2048)
            p = random.random()
            if p > LOSS:
                LOCK.acquire()
                
                r = parse_message(msg)
                print ('R: Received message from socket: at time: {0}'.format(TIMER))
                recieved_details(r)
                data_sent = False
                if r['seq'] is frame_expected:
                    # print ('R: Received expected frame: {0}'.format(r['seq']))
                    TIMER = current_milli_time()
                    print ('R: Timer Restarted {0}'.format(TIMER))
                    to_network_layer(r['info'])
                    frame_expected = (frame_expected + 1) % MAX_SEQ
                    ACK_READY = True

                if between(ack_expected, r['ack'], next_frame_to_send):
                    # print ('R: Received expected ack')
                    nbuffered = nbuffered - 1
                    ack_expected = (ack_expected + 1) % MAX_SEQ
                
                LOCK.release()
            else:
                print ('R: FRAME DROPPED')
        except socket.timeout:
            LOCK.acquire()
            print ('R: Received Timeout Error')
            TIMEUP = True
            LOCK.release()

def gobackn(socket, max_seq, start_first, loss):
    global next_frame_to_send
    global ack_expected
    global frame_expected
    global nbuffered
    global data_sent

    global NETWORK_LAYER_READY
    global SOCKET
    global MAX_SEQ
    global TIMEUP
    global TIMEOUT
    global TIMER
    global BASE_TIME
    global LOSS
    global ACK_READY

    LOSS = loss
    MAX_SEQ = max_seq
    ACK_READY = False
    TIMER = current_milli_time()
    SOCKET = socket
    buffer = []
    sender = start_first

    recv_thread = threading.Thread(target=recv_data)
    recv_thread.start()

    BASE_TIME = int(round(time.time() * 1000))
    while True:
        curr_time = current_milli_time()
        TIMEUP = curr_time-TIMER > TIMEOUT
        send_frame = ACK_READY or start_first
        
        if TIMEUP and sender:
            # Received timeout, re-send data
            LOCK.acquire()
            print ('S: Time up when next frame to be sent is {0}'.format(next_frame_to_send))
            TIMER = current_milli_time()
            print ('S: Timer Restarted {0}'.format(TIMER))
            TIMEUP = False
            if next_frame_to_send < MAX_SEQ:
                next_frame_to_send = 0
            else:
                next_frame_to_send = get_lowest_ack(next_frame_to_send-MAX_SEQ, ack_expected)
            
            print ('S: Re-sending from {0}'.format(next_frame_to_send))
            for i in range(nbuffered):
                send_data(next_frame_to_send, frame_expected, buffer)
                next_frame_to_send = next_frame_to_send + 1
            LOCK.release()
            
        if NETWORK_LAYER_READY and send_frame:
            print ('S: Sending frame: {0}'.format(next_frame_to_send))
            buffer.append(from_network_layer())
            LOCK.acquire()
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
