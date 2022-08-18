#! /usr/bin/env python

# Dan Pond 3/6/2019

# script for i2c master
# this script is configured for Relay interface board / RPi

import sys
import math
import time
import sys
import RPi.GPIO as GPIO

usage = "Usage: \n i2c_master.py <peek|poke> address [write_value]\n"


# Pin defs for Relay Interface adapter
I2C_SCL_PIN = 5
I2C_SDA_PIN = 3


# Note: internally values shall be passed integers (decimal).


# main function (for stand-alone testing)

def main():
    i2c_init()

#  PCT2075 test code - seems to work.
    dev_address = 0x49   # PCT2075

    command = i2c_cmd_prep(dev_address,1)

    i2c_start()
    i2c_tx_byte(command)
    #i2c_read_ack()
    value = i2c_rx_byte()
    i2c_stop()
    print "temperature={0:2d}C".format(value)
    sys.exit()




def i2c_cmd_prep(address,read):
    command = address << 1
    if (read):
        command |= 0x01

    return command

def i2c_scl_set(value):  # Set SCL pin to 0 or 1
    if (value):
        GPIO.setup(I2C_SCL_PIN, GPIO.IN)
    else:
        GPIO.setup(I2C_SCL_PIN, GPIO.OUT, initial=0)

def i2c_sda_set(value):  # Set SDA pin to 0 or 1
    if (value):
        GPIO.setup(I2C_SDA_PIN, GPIO.IN)
    else:
        GPIO.setup(I2C_SDA_PIN, GPIO.OUT, initial=0)

def i2c_sda_get():  # read the SDA pin value
    return GPIO.input(I2C_SDA_PIN)

def i2c_init():   # Put bus in known idle state
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    GPIO.setup([I2C_SCL_PIN,I2C_SDA_PIN], GPIO.IN)

def i2c_start():  # SDA falls while SCL high
    i2c_sda_set(0)
    i2c_scl_set(0)

def i2c_stop():   # SDA rises while SCL high
    i2c_scl_set(1)
    i2c_sda_set(1)

def i2c_ack():    # SDA low when SCL rises
    i2c_sda_set(0)
    i2c_scl_set(1)
    i2c_scl_set(0)

def i2c_noack():  # SDA high when SCL rises
    i2c_sda_set(1)
    i2c_scl_set(1)
    i2c_scl_set(0)

def i2c_tx_byte(write_value):  # master transmit 8 bits ...
    # value is assumed to be decimal string
    # need to convert to binary list
    data = list("{0:08b}".format(write_value))

    for bits in data:
        i2c_sda_set(int(bits))
        i2c_scl_set(1)
        i2c_scl_set(0)

    ack_val = i2c_read_ack()
    #print "debug: ack =",ack

    if (ack_val == 1):
        print "Error, no ACK"


def i2c_rx_byte():   # master receive 8 bits
    data = []

    for _ in range(8):
        data.append(i2c_sda_get())
        #print "debug data={}",data
        i2c_scl_set(1)
        i2c_scl_set(0)
        read_data = int("".join(map(str,data)),2)
        #print "debug: read data ={}".format(read_data,"x")
        #print "read_data={}".format(read_data)

    i2c_ack()
    return read_data

def i2c_read_ack():
    data = i2c_sda_get()
    i2c_scl_set(1)
    i2c_scl_set(0)
    return data


if __name__ == '__main__':
   sys.exit(main())

