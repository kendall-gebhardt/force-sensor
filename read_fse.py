import serial
import sys
import struct

ser = serial.Serial("/dev/ttyACM0")
ser.baudrate = 115200
ser.bytesize = serial.EIGHTBITS
ser.parity = serial.PARITY_NONE
ser.stopbits = serial.STOPBITS_ONE
ser.timeout = 1

stopCount = 100 #number of datapoints, later this will just wait until a buttonpress

raw = b'\x72'
force = b'\x66'
init = b'\x7a'
dataType = force

#initialize
#ser.write(dataType)
ser.write(init)
ser.close()

#create a text file
file = open("testfile.csv","w")

def getForce():
    print('start')
    ser.open()
    #wait for first byte 0x0D
    #while(chr.from_bytes(ser.read(size=1)) != '\r'):
    while(ser.read(size=1).decode() != '\r'):
        #print(str(struct.unpack('b', ser.read(size=1))))
        print(str(ser.read(size=1).decode()))

    size = struct.unpack('B',ser.read(size=1))
    mesgType = struct.unpack('s',ser.read(size=1))
    timeStamp = struct.unpack('>I', ser.read(size=4))
    forceX = struct.unpack('>f', ser.read(size=4))
    forceY = struct.unpack('>f', ser.read(size=4))
    forceZ = struct.unpack('>f', ser.read(size=4))
    stopByte = struct.unpack('>?', ser.read(size=1))
    ser.close()

    if (mesgType[0] == b'f'):
        messageType = "force"
    if (mesgType[0] == b'r'):
        messageType = "raw"

    triplet = [forceX[0], forceY[0], forceZ[0]]

    return triplet;

for i in range (stopCount):

    forces = getForce();
    #print(str(size[0]))
    #print(str(messageType))
    #print("Seconds: " + str(timeStamp[0]))
    #print("Force X: " + str(forceX[0]))
    #print("Force Y: " + str(forceY[0]))
    #print("Force Z: " + str(forceZ[0]))
    #print(str(stopByte[0]))
    print("Triplet: " + str(forces))
    file.write(str(forces[0]) + "," + str(forces[1]) + "," + str(forces[2]) + "\n")
    print('end')

file.close()


