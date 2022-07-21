#! /usr/bin/env python
# Author: Dan Pond
import sys
import math
import time
import sys
import RPi.GPIO as GPIO

usage = "Usage: \n admv.py <peek|poke> device address [write_value]\n"


DEV_ADDRESS = 0x23

I2C_SCL_PIN = 5
I2C_SDA_PIN = 3

SPI_SS_PIN   = 24
SPI_SCLK_PIN = 23
SPI_MOSI_PIN = 19
SPI_MISO_PIN = 21


# Note: internally values shall be passed integers (decimal).

# ADMV chip selects are controlled by an I2C IO expander (PCA9555)
# The chip selects are on port 1, bits [7:4]
# i2c_init:  
#   set all port 1 outputs to value 1.      write 0x23,0x3,0xff
#   set port 1 pins 7:4 to output type.  write 0x23,0x7,0x0f

# i2c_cleanup:
#   set all port 1 outputs to value 1       write 0x23,0x3,0xff
#   set port 1 pins 7:4 to input type.      write 0x23,0x7,0xff

# assert_csn
#   write 0 to appropriate bit.    write 0x23,0x3,value    (value = admv# + 4)

# deassert_csn
#   write 1 to all the outputs.    write 0x23,0x3,0xff


# Pseudo code
# parse command
# - issue I2C writes as needed to assert appropriate chip select
# - Create SPI address word (16 bits) - create send byte and read byte functions.
# - wiggle spi pins as needed to send word (+ data if write) and capture data if read. 
# - issue I2C writes as needed to shut off chip selects.  


def main():
    if len(sys.argv) < 4 or len(sys.argv) > 5:
        sys.exit(usage)

    # Process parameters - convert to integers
    device  = int(sys.argv[2],16) # Device number (0-3)
    address = int(sys.argv[3],16) # Register address (up to 15 bits)

    spi_init()
    i2c_init()
    pca9555_admv_init()

    if (sys.argv[1] == "peek"):
        spi_peek(device,address)

    elif (sys.argv[1] == "poke"):
        write_value = int(sys.argv[4],16) # Always hex input, convert to int
        spi_poke(device, address, write_value)

    else:
        sys.exit(usage)

    pca9555_admv_cleanup()
    spi_cleanup()
    i2c_init()
    sys.exit()


def spi_init():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    GPIO.setup([SPI_SS_PIN, SPI_SCLK_PIN, SPI_MOSI_PIN], GPIO.OUT)
    GPIO.setup(SPI_MISO_PIN, GPIO.IN)
    GPIO.output(SPI_SS_PIN, GPIO.HIGH)
    GPIO.output(SPI_SCLK_PIN, GPIO.LOW)
    GPIO.output(SPI_MOSI_PIN, GPIO.LOW)


def spi_cleanup():
    GPIO.setup([SPI_SS_PIN, SPI_SCLK_PIN, SPI_MOSI_PIN], GPIO.IN)


def spi_peek(device, address):
    # send address (16 bits)
    # capture 8-bit read value

    byte1 = (address >> 8) & 0xff | 0x80
    byte2 = address & 0xff

    GPIO.output(SPI_SCLK_PIN, 0)  # Set spi clock low
    select_admv(device)           # assert targeted ADMV csn

    send_byte(byte1)              # send upper address byte
    send_byte(byte2)              # send lower address byte
    data = read_byte()            # capture read data

    unselect_admv()               # de-assert ADMV csn
    #print "debug:{}".format(data)
    print "ADMV {:1d} READ A:0x{:04x} D:0x{:02x}".format(device, address, data)



def spi_poke(device,address,write_value):
    # calculate the 3 bytes to be written
    byte1 = (address >> 8) & 0x7F 
    byte2 = (address & 0xFF)
    byte3 = write_value

    GPIO.output(SPI_SCLK_PIN, 0)  # Set spi clock low
    select_admv(device)           # asserted targeted ADMV csn

    for i in (byte1,byte2,byte3):
        send_byte(i)

    unselect_admv()

    print "ADMV {:1d} WRITE A:0x{:04x} D:0x{:02x}".format(device,address,write_value)

def send_byte(value):

    # value is assumed to be decimal string
    # need to convert to binary list
    data = list("{0:08b}".format(value))

    for bits in data:
        GPIO.output(SPI_MOSI_PIN, int(bits)) # express data bit
        GPIO.output(SPI_SCLK_PIN, GPIO.HIGH) # clock high
        GPIO.output(SPI_SCLK_PIN, GPIO.LOW)  # clock low


def read_byte():
    GPIO.output(SPI_SCLK_PIN, 0)
    data = []

    for _ in range(8):
        data.append(GPIO.input(SPI_MISO_PIN))
        GPIO.output(SPI_SCLK_PIN, 1)
        GPIO.output(SPI_SCLK_PIN, 0)

    read_data = int("".join(map(str,data)),2)
    #print "read_data={}".format(read_data)

    return read_data


def pca9555_poke(address,data):
    i2c_start()
    i2c_cmd_send(DEV_ADDRESS,0)  # dev addr + WRITE
    i2c_tx_byte(address)         # write register address
    i2c_tx_byte(data)            # write data
    i2c_stop()
    print "PCA9555 reg write A:0x{:1x} D:0x{:02x}".format(address,data)


def pca9555_admv_init():
    i2c_init()
    pca9555_poke(3,0xff)
    pca9555_poke(7,0x0f)   # Enable bits 7:4 as outputs

def pca9555_admv_cleanup():
    pca9555_poke(7,0xff)
    pca9555_poke(3,0xff)
    i2c_init()

# assert_csn
#   write 0 to appropriate bit.    write 0x23,0x3,value    (value = admv# + 4)
def select_admv(device):
    if (device >= 4):
        sys.exit("Invalid ADMV device number")

    bit_number = (device + 4)
    bit_mask   = (~(1 << bit_number)) & 0xFF
    pca9555_poke(3,bit_mask)


def unselect_admv():
    pca9555_poke(0x3,0xff)

# If read == 1:  read command
# If read == 0:  write command
def i2c_cmd_send(address,read):
    command = address << 1

    if (read):
        command |= 0x01

    i2c_tx_byte(command)


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
    i2c_scl_set(1)  # this line allows use as repeat start also
    i2c_sda_set(0)
    i2c_scl_set(0)
    #print "I2C START"

def i2c_stop():   # SDA rises while SCL high
    i2c_scl_set(1)
    i2c_sda_set(1)
    #print "I2C STOP"


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
    #print "data=",data

    for bits in data:
        i2c_sda_set(int(bits))
        i2c_scl_set(1)
        i2c_scl_set(0)

    i2c_sda_set(1)
    ack_val = i2c_read_ack()
    #print "debug: ack =",ack

    if (ack_val == 1):
        print "no slave ACK"
    #else:
    #    print "slave ACK"

# Set not_last parameter to 1 if reading multiple bytes
def i2c_rx_byte(not_last):   # master receive 8 bits
    data = []

    for _ in range(8):
        data.append(i2c_sda_get())
        #print "debug data={}",data
        i2c_scl_set(1)
        i2c_scl_set(0)
        read_data = int("".join(map(str,data)),2)
        #print "debug: read data ={}".format(read_data,"x")
        #print "read_data={}".format(read_data)

    if (not_last):
        i2c_ack()
    else:
        i2c_noack()

    return read_data

def i2c_read_ack():
    data = i2c_sda_get()
    i2c_scl_set(1)
    i2c_scl_set(0)
    return data


if __name__ == '__main__':
   sys.exit(main())

