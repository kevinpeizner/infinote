from socket import *
#from sys import argv as ARGV

HOST = 'localhost'
PORT = 9999
CHUNK_SIZE = 4096

def exitdata(socket):
    socket.send('EXIT'.encode('utf-8'))

def getdata(data):
    return 'GET '+data[0]

def echodata(data):
    return 'ECHO '+' '.join(data)

socket = socket(AF_INET, SOCK_STREAM)
socket.connect((HOST, PORT))

print('Connected!')

while True:
    data = input('Enter cmd: ').split(' ')
    cmd = data[0].lower()
    msg = ''
    if cmd == 'exit':
        msg = exitdata(socket)
        break
    elif cmd == 'get':
        msg = getdata(data[1:])
    elif cmd == 'echo':
        msg = echodata(data[1:])
    else:
        print(cmd, ' not a recognized cmd.')
        continue
    socket.send(msg.encode('utf-8'))
    recv_reply = socket.recv(CHUNK_SIZE)
    while recv_reply and not 'done':
        print('GOT REPLY: ', recv_reply.decode('utf-8'))
        recv_reply = socket.recv(CHUNK_SIZE)

print('Exiting...')
socket.close()
