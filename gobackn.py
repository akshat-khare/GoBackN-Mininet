MAX_SEQ = 7

def between(a, b, c):
    bool abc = a<=b and b<c
    bool cab = c<a and a<=b
    bool bca = b<c and c<a
    if abc || cab || bca:
        return True
    return False

def send_data(frame_nr, frame_expected, buffer):
    s = {}
    s.info = buffer[frame_nr]
    s.seq = frame_nr
    s.ack = (frame_expected + MAX_SEQ) % (MAX_SEQ + 1)
    to_physical_layer(s)
    start_timer(frame_nr)

def gobackn():
    buffer = []

    next_frame_to_send = 0
    ack_expected = 0
    frame_expected = 0
    nbuffered = 0

    while True:
        wait_for_event(event)
        if event is network_layer_ready:
            buffer[next_frame_to_send] = from_network_layer()
            nbuffered = nbuffered + 1
            send_data(next_frame_to_send, frame_expected, buffer)
            next_frame_to_send = next_frame_to_send + 1
            break

        if event is frame_arrival:
            r = from_physical_layer()
            if r.seq is frame_expected:
                to_network_layer(r.info)
                frame_expected = frame_expected + 1
            while between(ack_expected, r.ack, next_frame_to_send):
                nbuffered = nbuffered - 1
                stop_timer(ack_expected)
                ack_expected = ack_expected + 1
            break

        if event is error:
            break

        if event is timeout:
            next_frame_to_send = ack_expected
            for i in range(nbuffered):
                send_data(next_frame_to_send, frame_expected, buffer)
                next_frame_to_send = next_frame_to_send + 1
        
        if nbuffered < MAX_SEQ:
            enable_network_layer()
        else
            disable_network_layer()
