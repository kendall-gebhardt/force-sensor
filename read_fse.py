###########################################################################
# This script is intended to run on a Raspberry Pi based waypoint training#
# block outfitted with an FSE103 capacitive force sensor. To use this     #
# device, power on the block by plugging the pi into the battery pack,    #
# Plug in the force sensor, and start this program via ssh from another   #
# computer. the resulting file can then be gathered via scp.              #
###########################################################################

import argparse
import datetime
import RPi.GPIO as GPIO
import serial
import struct
import sys
import time

""" Non public global variables """
_filename = ""
_negative_x_pin = 31
_positive_x_pin = 32
_negative_y_pin = 35
_positive_y_pin = 36
_negative_z_pin = 37
_positive_z_pin = 38
_power_pin = 29
_activity_pin = 33



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
        # set mode of hardware GPIOs to external pin numbering
        GPIO.setmode(GPIO.BOARD)

        # make LED gpios outputs
        led_pin_list = [_negative_x_pin,_positive_x_pin,_negative_y_pin, _positive_y_pin, 
                        _negative_z_pin, _positive_z_pin, _power_pin, _activity_pin]
        GPIO.setup(led_pin_list, GPIO.OUT)
    except Exception:
        print("Error setting up GPIOs")
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
    
    # use the boolean condition to turn pin on/off
    # this does not work for multicolor LED
    GPIO.output(_positive_x_pin, (forces[1] > force_threshold_x))
    GPIO.output(_negative_x_pin, (forces[1] < (force_threshold_x * -1)))
    GPIO.output(_positive_y_pin, (forces[2] > force_threshold_y))
    GPIO.output(_negative_y_pin, (forces[2] < (force_threshold_y * -1)))
    GPIO.output(_positive_z_pin, (forces[3] > force_threshold_z))
    GPIO.output(_negative_z_pin, (forces[3] < (force_threshold_z * -1)))

    positive_leds = [_positive_x_pin, _positive_y_pin, _positive_z_pin]
    negative_leds = [_negative_x_pin, _negative_y_pin, _negative_z_pin]

    #for i in range (len(forces)):
        #if forces[i] > force_threshold:
            #color = red
            #LED = positive[i]
        #if forces[i] < (force_threshold * -1):
            #color = red
            #LED = negative[i]
        #if forces[i] < force_threshold && forces[i] > touch_threshold:
            #color = green
            #LED = positive[i]
        #if forces[i] > (force_threshold * -1) && forces[i] < (touch_threshold * -1):
            #color = green
            #LED = negative[i]
        #else:
            #positive and negative of [i] are off

    # Toggle with
    # GPIO.output(pin, not GPIO.input(pin))

    return True

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

    while (current_time - start_time).total_seconds() < float(program_timeout * 60):
        
        current_time = datetime.datetime.now()
        
        try:
            if (current_time - last_reading).total_seconds() > interval:
                # Start activity and set the indicator as such
                GPIO.output(_activity_pin, True)
                
                # perform the read-->log-->indicate sequence
                forces = get_force()
                log_force(forces)
                indicate_status(forces)

                last_reading = current_time
                
                GPIO.output(_activity_pin, False) 
    
        except KeyboardInterrupt:
            # Quit cleanly if the user presses ^C
            print ("User interrupt...quitting...")
            GPIO.output(_activity_pin, False)
            GPIO.cleanup()
            s.close()
            #file.close()
            return False
            
    
    # Quit cleanly if the program times out
    print ("Program timed out...quitting...")
    GPIO.output(_activity_pin, False)
    GPIO.cleanup()
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
        s = serial.Serial(port='/dev/ttyACM0', baudrate=115200, timeout=0.1)
        print("Serial set...")
        # run init functions
        sensor_init(parsed_args.data_format)
        logs_init()
        indicator_init()
        GPIO.output(_power_pin, True)
        # Do the things!
        run_script(program_timeout=parsed_args.program_timeout)
    except Exception:
        print("Error")
        
    
        


    ####################################################
    #                       TODOs                      #
    # - Quit better when in the get_force() fcn
    # - 
    # - check usb device ID and vendor, compare to sensor
    # - 

    # Optional TODO is to switch the control of the LEDs from direct to I2C as in https://www.sparkfun.com/products/13884
        # or https://www.sparkfun.com/products/14038 (this one needs any two gpios and 5v power)
    # This may depend somewhat on if the LEDs will have their own board or if they will be hand soldered
    # I2C control does allow differentiation between light and hard touch -- will need different logic though
    # Power pin needs to be turned on outside of this script, preferably at the very end of the boot sequence
        # to show that it is ready to start logging
    # Have the pi shut down either 1) when the sensor is unplugged 2) when the script stops (or after copying the file?) 
        # 3) on a separate button press 4) ???
    # have automated workout call this function and start the script or
        # have automated workout give instructions to start the script and place the plate in handoff
        # either way, automatedworkout needs to know that the plate is coming from handoff and not the automation plate location
    # for hardware, check with hnin where the default location is for gripping deep well plates. it would be awesome if 
        # we could just tell the gantry it is a deep well and not have to onboard a new plate type

            #example#
    # ## Wait for valid input in while...not ###
    # is_valid=0
 
    # while not is_valid :
    #     try :
    #         choice = int ( raw_input('Enter your choice [1-3] : ') )
    #         ## set it to 1 to validate input and to terminate the while..not loop
    #         is_valid = 1 
    #     except ValueError, e :
    #         print ("'%s' is not a valid integer." % e.args[0].split(": ")[1])