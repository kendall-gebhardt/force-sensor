###########################################################################
# This script is intended to run on a Raspberry Pi based waypoint training#
# block outfitted with an FSE103 capacitive force sensor. To use this     #
# device, power on the block by plugging the pi into the battery pack,    #
# Plug in the force sensor, and start this program via ssh from another   #
# computer. the resulting file can then be gathered via scp.              #
###########################################################################

import argparse
import datetime
#import RPi.GPIO as GPIO
from sense_hat import SenseHat
import serial
import struct
import sys
import time

""" Non public global variables """
_filename = ""


def set_globals(filename):
    """Sets modular global variables"""
    global _filename
    _filename = 'logs/' + filename
    
    
    print ("Globals set...")
    return True

def sensor_init(data_format):
    """
    Runs the initialization sequence for the FSE103
    :param data_format: defined by user, default is force [N], 
                        describes how data is exported from the sensor
    :return: True when complete, false if no valid format is specified
    """
    # Set command bytes based on datasheet
    init_byte = b'\x7a'
    if data_format == 'raw':
        data_byte = b'\x72'
    if data_format == 'force':
        data_byte = b'\x66'
    else:
        print("not valid data format")
        return False

    # Initialize the sensor
    s.write(init_byte)
    # Later it would be good to include a 'zero' button that would send this init byte
    #s.write(data_byte)
    s.close()

    print ("Sensor initialized...")
    return True

def logs_init(): 
    """
    Create a csv to hold the data recorded from the force sensor
    :param _filename: defined as test-timestamp.csv
    :return: True when complete, false if error
    """
    # create a file and add column headers
    # I put the /logs/ directory in .gitignore but this may cause problems 
    try:
        with open(_filename,"w+") as file:
            file.write("Time, Force X, Force Y, Force Z\n")
    except IOError:
        print("Could not open file")
        return False

    print ("Logs initialized...")
    return True

def indicator_init():
    """
    Set up Raspberry Pi GPIOs to control indicator LEDs
    :param XXX: Uses global pin variables
    :return: True when complete, false if error
    """
    try:
        sense.set_rotation(0)
        sense.clear()
        sense.low_light = True
    except Exception:
        print("Error setting up LEDs")
        return False

    print ("Indicators initialized...")
    return True

def get_force():
    """
    Read one packet of data from the force sensor and format it into an array
    :param XXX: 
    :return: An array of data and hte timestamp of when it was taken
    """
    s.open()
    
    # wait for first byte 0x0D
    # this loop takes an unknown time so the time between data points should not be assumed
    while(s.read(size=1).decode() != '\r'):
        s.read(size=1).decode()
        
    # pick out data, sizes and types are from the datasheet
    size = struct.unpack('B',s.read(size=1))
    message_byte = struct.unpack('s',s.read(size=1))
    sensor_seconds = struct.unpack('>I', s.read(size=4))
    forceX = struct.unpack('>f', s.read(size=4))
    forceY = struct.unpack('>f', s.read(size=4))
    forceZ = struct.unpack('>f', s.read(size=4))
    stop_byte = struct.unpack('>?', s.read(size=1))
    
    s.close()

    # snag a timestamp of world time. Y-M-D is in the filename so we don't need that here
    time_stamp = datetime.datetime.now().strftime("%H:%M:%S.%f")

    # package data into an array
    dataOut = [time_stamp, forceX[0], forceY[0], forceZ[0]] 

    return dataOut;

def log_force(forces):
    """
    Take data array and append it to the end of the log csv
    :param forces: the array of data from get_force()
    :return: True when done, false if the file cannot be accessed
    """
    # Log data in terminal to show progress
    # print(str(forces))
    
    try:
        # write data to logfile
        with open(_filename, "a") as file:
            file.write(str(forces[0]) + "," + str(forces[1]) + "," 
                       + str(forces[2]) + "," + str(forces[3]) + "\n")
    except IOError:
        print("Error opening file")
        return False

    return True

def indicate_status(forces):
    """
    Light LEDs based on the force returned by the sensor
    :param forces: the array of data from get_force()
    :return: True when done
    """
    # turn on lights if force is over a threshold
    force_threshold_x = 2
    force_threshold_y = 2
    force_threshold_z = 5
    
    red = (255,0,0)
    off = (0,0,0)
    
    #  set border
    X = [0, 150, 0]  # light green
    O = [0, 0, 0]  # off

    border = [
    O, O, O, O, O, O, O, O,
    O, X, X, X, X, X, X, O,
    O, X, O, O, O, O, X, O,
    O, X, O, O, O, O, X, O,
    O, X, O, O, O, O, X, O,
    O, X, O, O, O, O, X, O,
    O, X, X, X, X, X, X, O,
    O, O, O, O, O, O, O, O
    ]
    
    sense.clear()
    
    if forces[3] > force_threshold_z:
        sense.set_pixels(border)
        
    if forces[1] > force_threshold_x:
        for i in range (0,8):
            sense.set_pixel(i, 7, red)
    if forces[1] < (-1 * force_threshold_x):
        for i in range (0,8):
            sense.set_pixel(i, 0, red)
    #if forces[1] > (-1 * force_threshold_x) and forces[1] < force_threshold_x:
        #sense.clear()
    if forces[2] > force_threshold_y:
        for i in range (0,8):
            sense.set_pixel(7, i, red)
    if forces[2] < (-1 * force_threshold_y):
        for i in range (0,8):
            sense.set_pixel(0, i, red)

    return True

def update_bubble(bubble):
    #  init bubble
    old_bubble = bubble
    prev_x1 = old_bubble[0]
    prev_x2 = old_bubble[1]
    prev_y1 = old_bubble[2]
    prev_y2 = old_bubble[3]
    
    accel_threshold = 0.1

    raw_Gs = sense.get_accelerometer_raw()
    x_Gs = raw_Gs['x']
    y_Gs = raw_Gs['y']
    z_Gs = raw_Gs['z']
    
    if x_Gs >= (-1 * accel_threshold) and x_Gs <= accel_threshold:
        x1 = 3
        x2 = 4
    if y_Gs >= (-1 * accel_threshold) and y_Gs <= accel_threshold:
        y1 = 3
        y2 = 4
        
    if x_Gs <= (-1 * accel_threshold):
        x1 = 4
        x2 = 5
    if y_Gs <= (-1 * accel_threshold):
        y1 = 4
        y2 = 5
        
    if x_Gs >= accel_threshold:
        x1 = 2
        x2 = 3
    if y_Gs >= accel_threshold:
        y1 = 2
        y2 = 3

    if x1 != prev_x1:
        sense.set_pixel(prev_x1, prev_y1, 0, 0, 0)
        sense.set_pixel(prev_x1, prev_y2, 0, 0, 0)
    if x2 != prev_x2:
        sense.set_pixel(prev_x2, prev_y1, 0, 0, 0)
        sense.set_pixel(prev_x2, prev_y2, 0, 0, 0)
    if y1 != prev_y1:
        sense.set_pixel(prev_x1, prev_y1, 0, 0, 0)
        sense.set_pixel(prev_x2, prev_y1, 0, 0, 0)
    if y2 != prev_y2:
        sense.set_pixel(prev_x1, prev_y2, 0, 0, 0)
        sense.set_pixel(prev_x2, prev_y2, 0, 0, 0)
    
    sense.set_pixel(x1, y1, 0, 0, 255)
    sense.set_pixel(x1, y2, 0, 0, 255)
    sense.set_pixel(x2, y1, 0, 0, 255)
    sense.set_pixel(x2, y2, 0, 0, 255)

    bubble = [x1, x2, y1, y2]
    
    return bubble

def run_script(program_timeout):
    """
    Runs the loop of get force-->log force-->indicate status for a defined time period
    :param program_timeout: From parsed args, default 20 min
    :return: whatever the function returns
    """
    print ("Logging force data, press ^C to quit")

    # Define interval, in seconds, for force readings
    interval = 0.25

    # log the start time of the loop for calculating timeout
    start_time = datetime.datetime.now()
    current_time = start_time
    last_reading = start_time
    
    # init accelerometer bubble
    bubble = [0 , 0, 0, 0]

    try:
        while (current_time - start_time).total_seconds() < float(program_timeout * 60):
        
            current_time = datetime.datetime.now()
        
            if (current_time - last_reading).total_seconds() > interval:
                # Start activity and set the indicator as such
                #GPIO.output(_activity_pin, True)
                
                # perform the read-->log-->indicate sequence
                forces = get_force()
                log_force(forces)
                indicate_status(forces)
                bubble = update_bubble(bubble)
                last_reading = current_time
                
                #GPIO.output(_activity_pin, False) 
    
    except KeyboardInterrupt:
        # Quit cleanly if the user presses ^C
        print ("User interrupt...quitting...")
        #GPIO.output(_activity_pin, False)
        sense.clear()
        s.close()
        #file.close()
        return False
            
    
    # Quit cleanly if the program times out
    print ("Program timed out...quitting...")
    #GPIO.output(_activity_pin, False)
   # GPIO.cleanup()
    return True



if __name__ == "__main__":
    """
    User interface and program init for running this script independently
    :param XXX: some useful info on what it is or where it's from
    :return: whatever the function returns
    """
    print ("Welcome to the waypoint trainer")
    # make the CLI
    parser = argparse.ArgumentParser(description="Script for running automated force logging.",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--program_timeout",
                        help="Maxiumum time for the program to run, in minutes",
                        default='20')

    parser.add_argument("--data_format",
                        help="Take readings in raw or calculated force values, type raw or force",
                        default='force')  

    parsed_args = parser.parse_args()
    
    # Try to initialize. Raise an error if initialization fails. 
    # All of this will need to be called in the external script if it is run that way
    try:
        # Initialize
        logfile = 'test-' + time.strftime("%Y%m%d-%H:%M:%S") + '.csv'        
        set_globals(filename=logfile)

        #find and open serial port here so the variable can be used globally
        port_array = []
        for i in range(256):
            try:
                #print(str(i))
                s = serial.Serial('/dev/ttyACM' + str(i))
                port_array.append((s.portstr))
                s.close()
            except:
                pass

        # Make sure the device is plugged in (at least one port is occupied)
        if len(port_array) == 0:
            print("No Available port. Ensure sensor is plugged in.")
        # Set the port to the first available port because we know only the sensor is plugged in
        # This is fragile and should be edited to check if the device matches ID: 16d0:0c21
        else:
            port = port_array[0]
            #print("Port: " + str(port))

        # set up the serial port 
        s = serial.Serial(port=port, baudrate=115200, timeout=0.1)
        print("Serial set...")
        # run init functions
        sense = SenseHat()
        
        sensor_init(parsed_args.data_format)
        logs_init()
        indicator_init()
        #GPIO.output(_power_pin, True)
        # Do the things!
        run_script(program_timeout=parsed_args.program_timeout)
    except Exception:
        raise
        
    
        


    ####################################################
    #                       TODOs                      #
    # - 
    # - 
    # - check usb device ID and vendor, compare to sensor
    # - 

    # Power pin needs to be turned on outside of this script, preferably at the very end of the boot sequence
        # to show that it is ready to start logging
    # Have the pi shut down either 1) when the sensor is unplugged 2) when the script stops (or after copying the file?) 
        # 3) on a separate button press 4) ???
    # have automated workout call this function and start the script or
        # have automated workout give instructions to start the script and place the plate in handoff
        # either way, automatedworkout needs to know that the plate is coming from handoff and not the automation plate location
    # for hardware, check with hnin where the default location is for gripping deep well plates. it would be awesome if 
        # we could just tell the gantry it is a deep well and not have to onboard a new plate type
