#!/usr/bin/env python2
# coding: utf-8

import os,socket,threading,time
import traceback
import random
import binascii
import subprocess
import sys
import shutil

import config

from aws.common.sqsqueue import Queue

vals = [
"\x00","\x01","\x02","\x03","\x04","\x05","\x06","\x07","\x08","\x09","\x0a","\x0b","\x0c","\x0d","\x0e","\x0f",
"\x10","\x11","\x12","\x13","\x14","\x15","\x16","\x17","\x18","\x19","\x1a","\x1b","\x1c","\x1d","\x1e","\x1f",
"\x20","\x21","\x22","\x23","\x24","\x25","\x26","\x27","\x28","\x29","\x2a","\x2b","\x2c","\x2d","\x2e","\x2f",
"\x30","\x31","\x32","\x33","\x34","\x35","\x36","\x37","\x38","\x39","\x3a","\x3b","\x3c","\x3d","\x3e","\x3f",
"\x40","\x41","\x42","\x43","\x44","\x45","\x46","\x47","\x48","\x49","\x4a","\x4b","\x4c","\x4d","\x4e","\x4f",
"\x50","\x51","\x52","\x53","\x54","\x55","\x56","\x57","\x58","\x59","\x5a","\x5b","\x5c","\x5d","\x5e","\x5f",
"\x60","\x61","\x62","\x63","\x64","\x65","\x66","\x67","\x68","\x69","\x6a","\x6b","\x6c","\x6d","\x6e","\x6f",
"\x70","\x71","\x72","\x73","\x74","\x75","\x76","\x77","\x78","\x79","\x7a","\x7b","\x7c","\x7d","\x7e","\x7f",
"\x80","\x81","\x82","\x83","\x84","\x85","\x86","\x87","\x88","\x89","\x8a","\x8b","\x8c","\x8d","\x8e","\x8f",
"\x90","\x91","\x92","\x93","\x94","\x95","\x96","\x97","\x98","\x99","\x9a","\x9b","\x9c","\x9d","\x9e","\x9f",
"\xa0","\xa1","\xa2","\xa3","\xa4","\xa5","\xa6","\xa7","\xa8","\xa9","\xaa","\xab","\xac","\xad","\xae","\xaf",
"\xb0","\xb1","\xb2","\xb3","\xb4","\xb5","\xb6","\xb7","\xb8","\xb9","\xba","\xbb","\xbc","\xbd","\xbe","\xbf",
"\xc0","\xc1","\xc2","\xc3","\xc4","\xc5","\xc6","\xc7","\xc8","\xc9","\xca","\xcb","\xcc","\xcd","\xcd","\xcf",
"\xd0","\xd1","\xd2","\xd3","\xd4","\xd5","\xd6","\xd7","\xd8","\xd9","\xda","\xdb","\xdc","\xdd","\xde","\xdf",
"\xe0","\xe1","\xe2","\xe3","\xe4","\xe5","\xe6","\xe7","\xe8","\xe9","\xea","\xeb","\xec","\xed","\xee","\xef",
"\xf0","\xf1","\xf2","\xf3","\xf4","\xf5","\xf6","\xf7","\xf8","\xf9","\xfa","\xfb","\xfc","\xfd","\xfe","\xff"]

allow_delete = False
local_ip = config.LOCAL_IP  #socket.gethostbyname(socket.gethostname())
local_port = config.LOCAL_PORT
currdir=os.path.abspath('.')

class FTPserverThread(threading.Thread):
    def __init__(self,(conn,addr)):
        self.conn=conn
        self.addr=addr
        self.basewd=currdir
        self.cwd=self.basewd
        self.rest=False
        self.pasv_mode=False
        threading.Thread.__init__(self)
        self.terminate = False

    def run(self):
        global COUNT
        self.conn.send('220 Welcome!\r\n')
        while True:
            try:
                cmd=self.conn.recv(256)
            except Exception,e:
                if str(e).find("Errno 10054") > -1 and COUNT < config.MAX_COUNT:
                    self.save_crash()
                    upload_crash_dir()
                    subprocess.Popen(["python", "pydbg_script.py"], stdout=subprocess.PIPE, cwd=os.getcwd())
                    for f in os.listdir(config.LOG_DIR):
                        os.remove("%s/%s" % (config.LOG_DIR, f))
            if not cmd: break
            else:
                print 'Recieved:',cmd
                try:
                    func=getattr(self,cmd[:4].strip().upper())
                    func(cmd)
                except Exception,e:
                    print 'ERROR:',e
                    traceback.print_exc()
                    self.conn.send('500 Sorry.\r\n')

    def save_crash(self):
        global DATA
        global COUNT
        fd = open("%s\\test_%s.bin" % (config.LOG_DIR, str(COUNT)), "wb")
        fd.write(DATA)
        fd.close()


    def SYST(self,cmd):
        self.conn.send('215 UNIX Type: L8\r\n')
    def OPTS(self,cmd):
        if cmd[5:-2].upper()=='UTF8 ON':
            self.conn.send('200 OK.\r\n')
        else:
            self.conn.send('451 Sorry.\r\n')
    def USER(self,cmd):
        self.conn.send('331 OK.\r\n')
    def PASS(self,cmd):
        self.conn.send('230 OK.\r\n')
        #self.conn.send('530 Incorrect.\r\n')
    def QUIT(self,cmd):
        self.conn.send('221 Goodbye.\r\n')
    def NOOP(self,cmd):
        self.conn.send('200 OK.\r\n')
    def TYPE(self,cmd):
        self.mode=cmd[5]
        self.conn.send('200 Binary mode.\r\n')

    def CDUP(self,cmd):
        if not os.path.samefile(self.cwd,self.basewd):
            #learn from stackoverflow
            self.cwd=os.path.abspath(os.path.join(self.cwd,'..'))
        self.conn.send('200 OK.\r\n')
    def PWD(self,cmd):
        cwd=os.path.relpath(self.cwd,self.basewd)
        if cwd=='.':
            cwd='/'
        else:
            cwd='/'+cwd
        self.conn.send('257 \"%s\"\r\n' % cwd)
    def CWD(self,cmd):
        chwd=cmd[4:-2]
        if chwd=='/':
            self.cwd=self.basewd
        elif chwd[0]=='/':
            self.cwd=os.path.join(self.basewd,chwd[1:])
        else:
            self.cwd=os.path.join(self.cwd,chwd)
        self.conn.send('250 OK.\r\n')

    def PORT(self,cmd):
        if self.pasv_mode:
            self.servsock.close()
            self.pasv_mode = False
        l=cmd[5:].split(',')
        self.dataAddr='.'.join(l[:4])
        self.dataPort=(int(l[4])<<8)+int(l[5])
        self.conn.send('200 Get port.\r\n')

    def PASV(self,cmd): # from http://goo.gl/3if2U
        self.pasv_mode = True
        self.servsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.servsock.bind((local_ip,0))
        self.servsock.listen(1)
        ip, port = self.servsock.getsockname()
        print 'open', ip, port
        self.conn.send('227 Entering Passive Mode (%s,%u,%u).\r\n' %
                (','.join(ip.split('.')), port>>8&0xFF, port&0xFF))

    def start_datasock(self):
        if self.pasv_mode:
            self.datasock, addr = self.servsock.accept()
            print 'connect:', addr
            if self.terminate == True:
                print "killing FTPserverThread"
                sys.exit(0)
        else:
            self.datasock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self.datasock.connect((self.dataAddr,self.dataPort))

    def stop_datasock(self):
        self.datasock.close()
        if self.pasv_mode:
            self.servsock.close()


    def LIST(self,cmd):
        global DATA
        global CRASH
        self.conn.send('150 Here comes the directory listing.\r\n')
        self.start_datasock()
        if CRASH:
            fd = open("bak\\last_test.bin", "rb")
            CRASH=False
        else:
            fd = open("%s" % config.MUTATION_FILE, "rb")

        DATA = fd.read()
        fd.close()
        self.datasock.send(mutate(DATA))
        self.stop_datasock()
        self.conn.send('226 Directory send OK.\r\n')

    def toListItem(self,fn):
        st=os.stat(fn)
        fullmode='rwxrwxrwx'
        mode=''
        for i in range(9):
            mode+=((st.st_mode>>(8-i))&1) and fullmode[i] or '-'
        d=(os.path.isdir(fn)) and 'd' or '-'
        ftime=time.strftime(' %b %d %H:%M ', time.gmtime(st.st_mtime))
        return d+mode+' 1 user group '+str(st.st_size)+ftime+os.path.basename(fn)

    def MKD(self,cmd):
        dn=os.path.join(self.cwd,cmd[4:-2])
        os.mkdir(dn)
        self.conn.send('257 Directory created.\r\n')

    def RMD(self,cmd):
        dn=os.path.join(self.cwd,cmd[4:-2])
        if allow_delete:
            os.rmdir(dn)
            self.conn.send('250 Directory deleted.\r\n')
        else:
            self.conn.send('450 Not allowed.\r\n')

    def DELE(self,cmd):
        fn=os.path.join(self.cwd,cmd[5:-2])
        if allow_delete:
            os.remove(fn)
            self.conn.send('250 File deleted.\r\n')
        else:
            self.conn.send('450 Not allowed.\r\n')

    def RNFR(self,cmd):
        self.rnfn=os.path.join(self.cwd,cmd[5:-2])
        self.conn.send('350 Ready.\r\n')

    def RNTO(self,cmd):
        fn=os.path.join(self.cwd,cmd[5:-2])
        os.rename(self.rnfn,fn)
        self.conn.send('250 File renamed.\r\n')

    def REST(self,cmd):
        self.pos=int(cmd[5:-2])
        self.rest=True
        self.conn.send('250 File position reseted.\r\n')

    def RETR(self,cmd):
        fn=os.path.join(self.cwd,cmd[5:-2])
        #fn=os.path.join(self.cwd,cmd[5:-2]).lstrip('/')
        print 'Downlowding:',fn
        if self.mode=='I':
            fi=open(fn,'rb')
        else:
            fi=open(fn,'r')
        self.conn.send('150 Opening data connection.\r\n')
        if self.rest:
            fi.seek(self.pos)
            self.rest=False
        data= fi.read(1024)
        self.start_datasock()
        while data:
            self.datasock.send(data)
            data=fi.read(1024)
        fi.close()
        self.stop_datasock()
        self.conn.send('226 Transfer complete.\r\n')

    def STOR(self,cmd):
        fn=os.path.join(self.cwd,cmd[5:-2])
        print 'Uplaoding:',fn
        if self.mode=='I':
            fo=open(fn,'wb')
        else:
            fo=open(fn,'w')
        self.conn.send('150 Opening data connection.\r\n')
        self.start_datasock()
        while True:
            data=self.datasock.recv(1024)
            if not data: break
            fo.write(data)
        fo.close()
        self.stop_datasock()
        self.conn.send('226 Transfer complete.\r\n')

class FTPserver(threading.Thread):
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((local_ip,local_port))
        threading.Thread.__init__(self)
        self.terminate = False

    def run(self):
        self.sock.listen(5)
        while True:
            th=FTPserverThread(self.sock.accept())
            th.daemon=True
            th.start()
            if self.terminate == True:
                th.terminate = True
                print "killing FTPserver"
                sys.exit(0)
                

    def stop(self):
        self.sock.close()

def get_string_mutations():
    strings = ["","/.:/" + "A" * 5000 + "\x00\x00","/.../" + "A" * 5000 + "\x00\x00","/" + ".../" * 10, "/" + "../" * 12 + "etc/passwd","/" + "../" * 12 + "boot.ini","..:" * 13,"\\\\*","\\\\?\\","/\\" * 5000,"//." * 5000,"!@#$%%^#$%#$%@#$%$$@#$%^^**(()","%01%02%03@%04%0a%0d%0aASDF", "//%00//","%00//","%00","%u0000","\x25\xfe\xf0\x25\x00\xff","\x25\xfe\xf0\x25\x01\xff" * 20,"%n" * 100,"%n" * 500,'"%n"' * 500,"%s" * 100,"%s" * 500,'"%s"' * 500,"touch tmp",";touch tmp;","notepad",";notepad;","\x0anotepad\x0a","1;SELECT%20*","'sqlattempt1","(sqlattempt2)","OR%201=1","\xDE\xAD\xBE\xEF","\xDE\xAD\xBE\xEF" * 10,"\xDE\xAD\xBE\xEF" * 100,"\xDE\xAD\xBE\xEF" * 1000,"\xDE\xAD\xBE\xEF" * 10000,"\x00" * 1000,"\x0d\x0a" * 100,"<>" * 500,]
    sizes = [127,128,255,256,257,511,512,513,1023,1024,1025,2048,2049,4096,4097,5000,10000,32762,32763,32764,32765,32766,32767,32768,32769,65533,65534,65535,65536,65537,99999,100000,500000,1000000]
    chars = ["A","B","1","2","3","<",">","'",'"',"/","\\","?","=","a=","&",",","(",")","]","[","%","*","-","+","{","}","\x14","\xfe","\xff",]
    for c in chars:
        for s in sizes:
            strings.append(c*s)
    strings.append("B"*64 + "\x00" + "B"*64)
    strings.append("B"*128 + "\x00" + "B"*128)
    strings.append("B"*512 + "\x00" + "B"*512)
    strings.append("B"*1024 + "\x00" + "B"*1024)
    strings.append("B"*2048 + "\x00" + "B"*2048)
    strings.append("B"*16384 + "\x00" + "B"*16384)
    strings.append("B"*32768 + "\x00" + "B"*32768)
    strings.append("SERVER"*2)
    strings.append("SERVER"*10)
    strings.append("SERVER"*100)
    strings.append("SERVER"*2 + "\xfe")
    strings.append("SERVER"*10 + "\xfe")
    strings.append("SERVER"*100 + "\xfe")
    return strings

def mutate(data):
    global DATA
    global COUNT
    if COUNT > config.MAX_COUNT:
        sys.exit(0)
    try:
        mut_type = config.MUTATION_TYPE
        if mut_type == 1:
            mutations = get_string_mutations()
            loc = random.randint(0, len(list(data))-1)
            mut = mutations[random.randint(0, len(mutations)-1)]
            data = list(data)
            data[loc] = mut
            data = "".join(data)

        if mut_type == 0:
            mut_len = random.randint(0, 10)
            loc = random.randint(0, len(list(data))-1)
            mut = ""
            for i in range(0, mut_len):
                mut += vals[random.randint(0, len(vals)-1)]
            data = list(data)
            data[loc] = mut
            data = "".join(data)

        print "Iteration = ", COUNT
        print "Offset = ", loc
        if mut_type == 0:
            print "FUZZ = '", binascii.hexlify(mut), "'"
        else:
            print "FUZZ = ", mut[0:10], "......"
        COUNT += 1
    except: 
        pass
    DATA = data
    return data

def upload_crash_dir():
    subprocess.call(["python", "aws\push.py", config.LOG_DIR])
    time.sleep(5)

def get_file_from_queue():
    queue = Queue()
    if queue.count() < 1:
        print "No more items in queue... exiting"
        sys.exit(0)
    m = queue.readone()
    print "Downloading file from S3",  m.get_body().split(",")[1]
    subprocess.call(["python", "aws\\pull.py", m.get_body().split(",")[1], "."])
    config.MUTATION_FILE = m.get_body().split(",")[1]
    queue.deleteone(m)


if __name__=='__main__':
    global DATA
    global COUNT
    global CRASH
    get_file_from_queue()
    CRASH = False
    COUNT = 0
    ftp=FTPserver()
    ftp.daemon=True
    ftp.start()
    print 'On', local_ip, ':', local_port
    subprocess.Popen(["python", "pydbg_script.py"], stdout=subprocess.PIPE, cwd=os.getcwd())
    while True:
        if COUNT > config.MAX_COUNT:
            subprocess.call(["taskkill", "/f", "/im", config.IMAGE_NAME])
            ftp.terminate = True
            ftp.stop()
            sys.exit(0)
        if raw_input("press enter to crash..."):
            CRASH = True

