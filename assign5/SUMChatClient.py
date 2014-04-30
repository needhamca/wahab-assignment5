#!/usr/bin/python
#Christopher Needham
#Assignment 2
#CS 779

import socket
import sys
import signal
import getpass
import time
import select
import sctp

shost = str(sys.argv[1])
sport = int(sys.argv[2])
clientType = str(sys.argv[3])

BUFFER_SIZE = 1024

#Create a TCP socket to connect to server
serverTCPConnection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverTCPConnection.connect((shost, sport))
connectionIP = shost
connectionPort= sport
print 'Starting connection wait 3 seconds'

#Sending username and client type
serverTCPConnection.send(getpass.getuser())
time.sleep(1)
if clientType == 'm' :
    #receive information to connect
    serverTCPConnection.send('0')
    connectionIP = serverTCPConnection.recv(BUFFER_SIZE)
    connectionPort = int(serverTCPConnection.recv(BUFFER_SIZE))
    LNUMBER = serverTCPConnection.recv(BUFFER_SIZE)
    ENUMBER = serverTCPConnection.recv(BUFFER_SIZE)
elif clientType == 'u':
    serverTCPConnection.send('1')
    connectionPort = int(serverTCPConnection.recv(BUFFER_SIZE))
    LNUMBER = serverTCPConnection.recv(BUFFER_SIZE)
    ENUMBER = serverTCPConnection.recv(BUFFER_SIZE)
else:
    serverTCPConnection.send('2')
    connectionPort = int(serverTCPConnection.recv(BUFFER_SIZE))
    LNUMBER = serverTCPConnection.recv(BUFFER_SIZE)
    ENUMBER = serverTCPConnection.recv(BUFFER_SIZE)
    
sendSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#create the sending socket.
outgoing = (connectionIP, connectionPort)
if clientType != 's' :
    sendSocket.bind((serverTCPConnection.getsockname()[0], serverTCPConnection.getsockname()[1]));
    sendSocket.connect(outgoing)
else :
    sendSocket = sctp.sctpsocket_udp(socket.AF_INET)
    sendSocket.bind((serverTCPConnection.getsockname()[0], serverTCPConnection.getsockname()[1]));
    sendSocket.listen(1)


if clientType == 'm':
    #Creating a multicat address to listen to.
    receiveSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receiveSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    receiveSocket.bind((connectionIP, connectionPort))
    host = socket.gethostbyname(socket.gethostname())
    receiveSocket.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(host))
    receiveSocket.setsockopt(socket.SOL_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(connectionIP) + socket.inet_aton(host))
else:
    #Using sendsocket as the receiving socket if it is a unicast client.
    receiveSocket = sendSocket



#sent request for list
def ctrlcHandler(signum, frame):
    sendSocket.sendto(LNUMBER,(outgoing))
    
print '################################################'
print 'User Name = ' + getpass.getuser()
print 'Receiving from', receiveSocket.getsockname()
print 'Sending from ', sendSocket.getsockname()
print 'Using outgoing address', outgoing
print 'L =' + str(LNUMBER) +'   E =' + str(ENUMBER)
print '################################################'
print ' '
print ' '

def close():
    print 'Closing'
    serverTCPConnection.close()
    sendSocket.sendto(ENUMBER, (outgoing))
    sendSocket.close()
    if receiveSocket != sendSocket :
        receiveSocket.close()
    sys.exit()  


signal.signal(signal.SIGINT, ctrlcHandler)
while True:
    try:
        inputs, outputs, errors = select.select([receiveSocket, sys.stdin], [], [])
        for input in inputs:
            if input == receiveSocket :
                packet = receiveSocket.recvfrom(BUFFER_SIZE)
                print ''
                #If its a disconnect message print info
                if packet[0] == ENUMBER:
                    print packet[1], ' is Disconnecting' 
                else :
                    #if normal message print data
                    print 'From:  ', packet[0] 
            elif input == sys.stdin :
                #read from standard in and send it to connection
                message = sys.stdin.readline()
                if not message or message == '':
                    close()
                else :
                    sendSocket.sendto(message,(outgoing))
    except select.error:
        pass
        