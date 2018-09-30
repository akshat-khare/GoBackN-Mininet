import socket
import sys

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
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                conn.sendall(data)    

if __name__ == '__main__':
    main()