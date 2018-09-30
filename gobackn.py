MAX_SEQ = 7
global SOCKET
global ADDR
NETWORK_LAYER_READY = True

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
    # Todo -> Parse the message and return a dictionary of seq_num, info and ack
    r = {}
    r['seq'] = 0
    r['info'] = '0000000'
    r['ack'] = 0
    return r

def send_data(frame_nr, frame_expected, buffer):
    global ADDR
    s = {}
    s['info'] = buffer[frame_nr]
    s['seq'] = frame_nr
    s['ack'] = (frame_expected + MAX_SEQ) % (MAX_SEQ + 1)
    # Todo -> Construct the string to be sent
    msg = '0010001'
    SOCKET.sendto(msg, ADDR)
    # Start the timer thread

def gobackn(socket):
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

def main():
    pass

if __name__ == '__main__':
    main()