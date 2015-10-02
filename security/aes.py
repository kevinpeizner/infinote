import base64
import os.path # remove in production, only for testing?
from sys import argv as ARGV # remove from production, only for testing?
from os import urandom
from Crypto.Cipher import AES
from Crypto.Hash import SHA256

class AESCipher:
    def __init__(self, passphrase):
        self.set_key(passphrase)

    def set_key(self, passphrase):
        if(type(passphrase) is str):
            print('\nPassphrase is a string. Converting to byte sequence before keygen.')
            passphrase = passphrase.encode('utf-8')
        elif(type(passphrase) is not bytes):
            print('\nPassphrase must be a string or a byte sequence. -- no key generated!')
            return
        hasher = SHA256.new(passphrase)
        self.key = hasher.digest()
        print('\nKey generated:')
        print(self.key)


    # PKCS#7 padding
    def __pad(self, data):
        pad_len = AES.block_size - len(data) % AES.block_size
        if pad_len == 0:
            pad_len = 16
        return data + (chr(pad_len)*pad_len).encode('utf-8')

    def __unpad(self, data):
        pad_len = ord(data[-1:].decode('utf-8'))
        return data[:-pad_len]

    def encrypt(self, raw):
        if type(raw) is not bytes:
            print('Raw data is not in raw bytes! -- Will not encrypt.') ## TODO throw exp
        raw = self.__pad(raw)
        iv = urandom(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:16]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self.__unpad(cipher.decrypt(enc[16:]))

def test_file(cipher, pwd, filename):
    ext = os.path.splitext(filename)[1]
    print(ext)

    infile = open(filename, 'rb')
    outfile = open(filename+'.crypt', 'wb')
    
    data = infile.read()
    infile.close()
    
    cyphertext = cipher.encrypt(data)
    outfile.write(cyphertext)
    outfile.close()
    
    infile = open(filename+'.crypt', 'rb')
    cyphertext2 = infile.read()
    infile.close()

    plaintext = cipher.decrypt(cyphertext)
    outfile = open('result'+ext, 'wb')
    outfile.write(plaintext)
    outfile.close()

def test(cipher, pwd):
    data = 'This is a test'
    print('\nPlaintext:')
    print(data)
    cydata = cipher.encrypt(data.encode('utf-8'))
    print('\nCyphertext:')
    print(cydata)
    res = cipher.decrypt(cydata).decode('utf-8')
    print('\nResult:')
    print(res)
    print('\nDone!\n\n')

def main():    
    pwd = input('Give me a password:\n')
    cipher = AESCipher(pwd)
    
    if len(ARGV) > 1 and os.path.isfile(ARGV[1]):
        test_file(cipher, pwd, ARGV[1])
    else:
        test(cipher, pwd)


if __name__ == "__main__":
    main()
