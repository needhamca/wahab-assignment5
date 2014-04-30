#!/usr/bin/python
#Christopher Needham
#Assignment 2
#CS 779

import sys
import socket
import random
import signal
import select
import sctp

import time

#Generate the Multi cast ip, port, L, and E values
BUFFER_SIZE = 1024
MULTI_CAST_IP = str(random.randint(224,239)) +  '.' + str(random.randint(0, 255))  +  '.' + str(random.randint(0, 255))  +  '.' + str(random.randint(0, 255))
MULTI_CAST_PORT = random.randint(9999, 11001)
LNUMBER = random.randint(1000000,9999999)
ENUMBER = random.randint(1000000,9999999)
sport = int(sys.argv[1])
host = socket.gethostbyname(socket.gethostname())

print 'Host:   ', host,    'port:   ', sport
print 'SCTP/UNICAST Host: ', host, 'port: ', MULTI_CAST_PORT
print 'Multicast Host: ', MULTI_CAST_IP, 'Multicast port: ', MULTI_CAST_PORT
print 'L  = ', LNUMBER
print 'E  = ', ENUMBER

#create the UDP socket to relay messages to other clients
udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
udpSocket.bind(('', MULTI_CAST_PORT))
udpSocket.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(host))
udpSocket.setsockopt(socket.SOL_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(MULTI_CAST_IP) + socket.inet_aton(host))



#create the SCTP socket
stcpSocket = sctp.sctpsocket_udp(socket.AF_INET)
stcpSocket.bind(('', MULTI_CAST_PORT))
stcpSocket.listen(1)

#create the TCP sockets that clients will use to connect to the server
tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpSocket.bind(('', sport))
tcpSocket.listen(1)



mlist = []
ulist = []
slist = []
    

#Methond for building client list string
def getListString():
    s =  '----Multicast ----\n'
    for m in mlist:
        s +=  str(m) +'\n'
    s += '-----Unicast ----\n'
    for u in ulist:
        s +=  str(u) +'\n'
        
    s += '-----Scpt ----\n'
    for j in slist:
        s +=  str(j) +'\n'
    return s


#Signal handler for Ctrl-c    
def handler(signum, frame):
    print getListString()
  

#Signal handler for ctrl-\               
def close(signum, frame):
    try:
        for item in ulist:
            udpSocket.sendto(str(ENUMBER), item[0])
        udpSocket.sendto(str(ENUMBER), (MULTI_CAST_IP,MULTI_CAST_PORT ))
        tcpSocket.close()
        udpSocket.close()
        print 'Closing'
    except socket.error as (code, message):
        pass
    sys.exit()

#Register signal handlers
signal.signal(signal.SIGINT, handler)
signal.signal(signal.SIGQUIT, close)
    
while True:
    try :
        inputs, outputs, errors = select.select([udpSocket, tcpSocket, stcpSocket], [], [])
        for input in inputs:
            if input == tcpSocket:  
                #Accepting tcp client connections
                connection, address = tcpSocket.accept()
                userName = connection.recv(BUFFER_SIZE)
                message = connection.recv(BUFFER_SIZE)
                if message == '0':
                    #If the client is a multicast client add it to mlist
                    print 'Accepting multicast connection ' ,userName, address 
                    connection.send(str(MULTI_CAST_IP))
                    time.sleep(1) # accepts time in secs 
                    connection.send(str(MULTI_CAST_PORT))
                    time.sleep(1) # accepts time in secs 
                    connection.send(str(LNUMBER))
                    time.sleep(1) # accepts time in secs 
                    connection.send(str(ENUMBER))
                    mlist.append((address,userName))
                elif message  == '1':
                    #If the client is a unicast client add it to ulist
                    print 'Accepting unicast connection ' ,address 
                    connection.send(str(MULTI_CAST_PORT))
                    time.sleep(1) # accepts time in secs 
                    connection.send(str(LNUMBER))
                    time.sleep(1) # accepts time in secs 
                    connection.send(str(ENUMBER))
                    ulist.append((address,userName))
                elif message == "2":
                    #If the client is a sctp client add it to slist
                    print 'Accepting sctp connection ' ,address 
                    connection.send(str(MULTI_CAST_PORT))
                    time.sleep(1) # accepts time in secs 
                    connection.send(str(LNUMBER))
                    time.sleep(1) # accepts time in secs 
                    connection.send(str(ENUMBER))
                    slist.append((address,userName))
            else : 
                packet = input.recvfrom(BUFFER_SIZE)
                #Answer list request messages
                if packet[0] == str(LNUMBER) :
                    for item in ulist :                
                        if item[0] == packet[1] :
                            udpSocket.sendto(getListString(), packet[1])
                    for item in mlist :
                        if item[0] == packet[1] :
                            udpSocket.sendto(getListString(), (MULTI_CAST_IP,MULTI_CAST_PORT ))
                    for item in slist :
                        if item[0] == packet[1] :
                            stcpSocket.sendto(getListString(), packet[1])
                #Answer disconnection messages
                elif packet[0] == str(ENUMBER) :
                    for item in ulist :                
                        if item[0] == packet[1] :
                            print 'Unicast client ', packet[1], 'is disconnecting'
                            ulist.remove(item)
                    for item in mlist :
                        if item[0] == packet[1] :
                            print 'Multicast client ', packet[1], 'is disconnecting'
                            mlist.remove(item)
                    for item in slist :
                        if item[0] == packet[1] :
                            print 'SCTP client ', packet[1], 'is disconnecting'
                            slist.remove(item)
                else:
                    #Print and relay normal messages.
                    print ''
                    print 'From: ', packet[1] 
                    print packet[0]    
                    for connection in ulist :                
                        if connection[0] == packet[1] :
                            for items in ulist :
                                udpSocket.sendto(str(packet[1]) +" "+ packet[0], items[0])
                            for items in slist :
                                stcpSocket.sendto(str(packet[1]) +" "+packet[0], items[0])
                            udpSocket.sendto(packet[0], (MULTI_CAST_IP,MULTI_CAST_PORT ))
            
                    for connection in mlist :                
                        if connection[0] == packet[1] :
                            for items in ulist :
                                udpSocket.sendto(str(packet[1]) +" "+packet[0], items[0])
                            for items in slist :
                                stcpSocket.sendto(str(packet[1]) +" "+packet[0], items[0])
                                
                    for connection in slist :
                        if connection[0] == packet[1] :
                            for items in slist :
                                stcpSocket.sendto(str(packet[1]) +" "+packet[0], items[0])
                            for items in ulist :
                                udpSocket.sendto(str(packet[1]) +" "+packet[0], items[0])
                            udpSocket.sendto(str(packet[1]) +" "+packet[0], (MULTI_CAST_IP,MULTI_CAST_PORT ))

    except select.error:
        pass