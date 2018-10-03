import serial
import sys
import struct

#set up the serial port
#need a 'try' function to find the right usb port
ser = serial.Serial("/dev/ttyACM0")
ser.baudrate = 115200
ser.bytesize = serial.EIGHTBITS
ser.parity = serial.PARITY_NONE
ser.stopbits = serial.STOPBITS_ONE
ser.timeout = 1

#define how many datapoints to take
stopCount = 100
#later this will just wait until an interrupt

#These commands are from the datasheet
raw = b'\x72'
force = b'\x66'
init = b'\x7a'

#specify data type for this reading
dataType = force

#initialize the sensor
ser.write(init)
ser.close()

#create a text file and add column headers
#I put the /logs/ directory in .gitignore but this may cause problems later
file = open("logs/testfile.csv","w")
file.write("Time, Force X, Force Y, Force Z\n")

#define a function for grabbing data
def getForce():
    
    ser.open()
    
    #wait for first byte 0x0D
    while(ser.read(size=1).decode() != '\r'):
        ser.read(size=1).decode()
        
    #pick out data packets, sizes and types are from the datasheet
    size = struct.unpack('B',ser.read(size=1))
    mesgType = struct.unpack('s',ser.read(size=1))
    timeStamp = struct.unpack('>I', ser.read(size=4))
    forceX = struct.unpack('>f', ser.read(size=4))
    forceY = struct.unpack('>f', ser.read(size=4))
    forceZ = struct.unpack('>f', ser.read(size=4))
    stopByte = struct.unpack('>?', ser.read(size=1))
    
    ser.close()
    
    #Hacky way to check message type
    if (mesgType[0] == b'f'):
        messageType = "force"
    if (mesgType[0] == b'r'):
        messageType = "raw"

    #package data into an array
    dataOut = [timeStamp[0], forceX[0], forceY[0], forceZ[0]]

    return dataOut;

for i in range (stopCount):

    forces = getForce();
    
    #Log data in terminal to show progress
    print(str(forces))
    
    #write data to logfile
    file.write(str(forces[0]) + "," + str(forces[1]) + "," + str(forces[2]) + "," + str(forces[3]) + "\n")

#close file when done
file.close()


