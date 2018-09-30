import socket
import sys
import gobackn

HOST = str(sys.argv[1])     # The server's hostname or IP address
PORT = int(sys.argv[2])     # Port used by server
LOSS = float(sys.argv[3])   # Loss probability

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(b'Hello, world')
        data = s.recv(1024)
        print('Received', repr(data))
        
        print('Starting go back n')
        gobackn.gobackn(s, False)
        print('Go back n completed')
    

if __name__ == '__main__':
    main()