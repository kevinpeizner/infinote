import http.server
import socketserver
import time
import ripper

HOST = ''
PORT = 9999
CHUNK_SIZE = 1024

def now():
    return time.ctime(time.time())

class ClientHandler(socketserver.BaseRequestHandler):

    def progress_cb(total, recvd, ratio, rate, eta):
        prg_stats = (recvd, ratio, rate, eta)
        status = ripper.status_string.format(*prg_stats)
        ClientHandler.sckt.send(status.encode('utf-8'))
    
    def handledata(self, data):
        reply = ''
        decodeddata = data.decode('utf-8').split(' ')
        cmd = decodeddata[0].lower()
        print('Handling cmd: ', cmd)
        if cmd == 'exit':
            reply = 'exit'
        elif cmd == 'echo':
            reply = 'Echo => '+data.decode('utf-8')
        elif cmd == 'get':
            ClientHandler.sckt = self.request
            ripper.getaudio(decodeddata[1], '.')
            reply = 'done'

        return reply

    def handle(self):
        print(self.client_address, now())
        while True:
            data = self.request.recv(CHUNK_SIZE)
            if not data:
                break
            reply = self.handledata(data)
            print('REPLYING: ', reply)
            self.request.send(reply.encode('utf-8'))
            if reply == 'exit':
                break

        print('Bye-bye ', self.client_address)
        self.request.close()

print(ripper.progress_cb)
ripper.progress_cb = ClientHandler.progress_cb
print(ripper.progress_cb)

server = socketserver.ThreadingTCPServer((HOST, PORT), ClientHandler)
server.allow_reuse_address = True
server.serve_forever()
