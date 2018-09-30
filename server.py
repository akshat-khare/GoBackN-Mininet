import socket
import sys
import gobackn

HOST = str(sys.argv[1])     # Standard loopback interface address (localhost)
PORT = int(sys.argv[2])     # Port to listen on (non-privileged ports are > 1023)
LOSS = float(sys.argv[3])   # Loss probability

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        conn, addr = s.accept()
        with conn:
            print('Connected by', addr)
            data = conn.recv(1024)
            conn.sendall(data)

            print('Starting go back n')
            gobackn.gobackn(conn, True)
            print('Go back n completed')

if __name__ == '__main__':
    main()