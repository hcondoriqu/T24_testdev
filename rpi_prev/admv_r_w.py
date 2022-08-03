#! /usr/bin/env python
# Author: Dan Pond
import sys
import math
import time
import sys
import RPi.GPIO as GPIO


class SPI_ADMV:
    def __init__(self, spi_type):
        """Define pins based on cpld_type"""
        if spi_type.lower() == "admv":
            self.dev_address = 0x23
            self.i2c_scl = 5
            self.i2c_sda = 3

            self.ss_pin = 24
            self.sclk_pin = 23
            self.mosi_pin = 19
            self.miso_pin = 21
            self.type = "admv"
        self.spi_init()
        self.i2c_init()
        self.pca9555_admv_init()

    def spi_init(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        GPIO.setup([self.ss_pin, self.sclk_pin, self.mosi_pin], GPIO.OUT)
        GPIO.setup(self.miso_pin, GPIO.IN)
        GPIO.output(self.ss_pin, GPIO.HIGH)
        GPIO.output(self.sclk_pin, GPIO.LOW)
        GPIO.output(self.mosi_pin, GPIO.LOW)

    def spi_cleanup(self):
        GPIO.setup([self.ss_pin, self.sclk_pin, self.mosi_pin], GPIO.IN)

    def spi_peek(self, device, address):
        # send address (16 bits)
        # capture 8-bit read value

        byte1 = (address >> 8) & 0xFF | 0x80
        byte2 = address & 0xFF

        GPIO.output(self.sclk_pin, 0)  # Set spi clock low
        self.select_admv(device)  # assert targeted ADMV csn

        self.send_byte(byte1)  # send upper address byte
        self.send_byte(byte2)  # send lower address byte
        data = self.read_byte()  # capture read data

        self.unselect_admv()  # de-assert ADMV csn
        # print "debug:{}".format(data)
        # print("ADMV {:1d} READ A:0x{:04x} D:0x{:02x}".format(device, address, data))
        return data

    def spi_poke(self, device, address, write_value):
        # calculate the 3 bytes to be written
        byte1 = (address >> 8) & 0x7F
        byte2 = address & 0xFF
        byte3 = write_value

        GPIO.output(self.sclk_pin, 0)  # Set spi clock low
        self.select_admv(device)  # asserted targeted ADMV csn

        for i in (byte1, byte2, byte3):
            self.send_byte(i)

        self.unselect_admv()

        # print( 
        #     "ADMV {:1d} WRITE A:0x{:04x} D:0x{:02x}".format(
        #         device, address, write_value
        #     )
        # )

    def send_byte(self, value):

        # value is assumed to be decimal string
        # need to convert to binary list
        data = list("{0:08b}".format(value))

        for bits in data:
            GPIO.output(self.mosi_pin, int(bits))  # express data bit
            GPIO.output(self.sclk_pin, GPIO.HIGH)  # clock high
            GPIO.output(self.sclk_pin, GPIO.LOW)  # clock low

    def read_byte(self):
        GPIO.output(self.sclk_pin, 0)
        data = []

        for _ in range(8):
            data.append(GPIO.input(self.miso_pin))
            GPIO.output(self.sclk_pin, 1)
            GPIO.output(self.sclk_pin, 0)

        read_data = int("".join(map(str, data)), 2)
        # print "read_data={}".format(read_data)

        return read_data

    def pca9555_poke(self, address, data):
        self.i2c_start()
        self.i2c_cmd_send(self.dev_address, 0)  # dev addr + WRITE
        self.i2c_tx_byte(address)  # write register address
        self.i2c_tx_byte(data)  # write data
        self.i2c_stop()
        # print("PCA9555 reg write A:0x{:1x} D:0x{:02x}".format(address, data))

    def pca9555_admv_init(self):
        self.i2c_init()
        self.pca9555_poke(3, 0xFF)
        self.pca9555_poke(7, 0x0F)  # Enable bits 7:4 as outputs

    def pca9555_admv_cleanup(self):
        self.pca9555_poke(7, 0xFF)
        self.pca9555_poke(3, 0xFF)
        self.i2c_init()

    # assert_csn
    #   write 0 to appropriate bit.    write 0x23,0x3,value    (value = admv# + 4)
    def select_admv(self, device):
        if device >= 4:
            sys.exit("Invalid ADMV device number")

        bit_number = device + 4
        bit_mask = (~(1 << bit_number)) & 0xFF
        self.pca9555_poke(3, bit_mask)

    def unselect_admv(self):
        self.pca9555_poke(0x3, 0xFF)

    # If read == 1:  read command
    # If read == 0:  write command
    def i2c_cmd_send(self, address, read):
        command = address << 1

        if read:
            command |= 0x01

        self.i2c_tx_byte(command)

    def i2c_scl_set(self, value):  # Set SCL pin to 0 or 1
        if value:
            GPIO.setup(self.i2c_scl, GPIO.IN)
        else:
            GPIO.setup(self.i2c_scl, GPIO.OUT, initial=0)

    def i2c_sda_set(self, value):  # Set SDA pin to 0 or 1
        if value:
            GPIO.setup(self.i2c_sda, GPIO.IN)
        else:
            GPIO.setup(self.i2c_sda, GPIO.OUT, initial=0)

    def i2c_sda_get(self):  # read the SDA pin value
        return GPIO.input(self.i2c_sda)

    def i2c_init(self):  # Put bus in known idle state
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        GPIO.setup([self.i2c_scl, self.i2c_sda], GPIO.IN)

    def i2c_start(self):  # SDA falls while SCL high
        self.i2c_scl_set(1)  # this line allows use as repeat start also
        self.i2c_sda_set(0)
        self.i2c_scl_set(0)
        # print "I2C START"

    def i2c_stop(self):  # SDA rises while SCL high
        self.i2c_scl_set(1)
        self.i2c_sda_set(1)
        # print "I2C STOP"

    def i2c_ack(self):  # SDA low when SCL rises
        self.i2c_sda_set(0)
        self.i2c_scl_set(1)
        self.i2c_scl_set(0)

    def i2c_noack(self):  # SDA high when SCL rises
        self.i2c_sda_set(1)
        self.i2c_sda_set(1)
        self.i2c_sda_set(1)
        self.i2c_sda_set(1)
        self.i2c_scl_set(1)
        self.i2c_scl_set(0)

    def i2c_tx_byte(self, write_value):  # master transmit 8 bits ...
        # value is assumed to be decimal string
        # need to convert to binary list
        data = list("{0:08b}".format(write_value))
        # print "data=",data

        for bits in data:
            self.i2c_sda_set(int(bits))
            self.i2c_scl_set(1)
            self.i2c_scl_set(0)

        self.i2c_sda_set(1)
        ack_val = self.i2c_read_ack()
        # print "debug: ack =",ack

        if ack_val == 1:
            # print("no slave ACK")
        # else:
        #    print "slave ACK"

    # Set not_last parameter to 1 if reading multiple bytes
    def i2c_rx_byte(self, not_last):  # master receive 8 bits
        data = []

        for _ in range(8):
            data.append(i2c_sda_get())
            # print "debug data={}",data
            self.i2c_scl_set(1)
            self.i2c_scl_set(0)
            read_data = int("".join(map(str, data)), 2)
            # print "debug: read data ={}".format(read_data,"x")
            # print "read_data={}".format(read_data)

        if not_last:
            self.i2c_ack()
        else:
            self.i2c_noack()

        return read_data

    def i2c_read_ack(self):
        data = self.i2c_sda_get()
        self.i2c_scl_set(1)
        self.i2c_scl_set(0)
        return data

    def cleanup(self):
        self.pca9555_admv_cleanup()
        self.spi_cleanup()
        self.i2c_init()


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
    #
    return None


if __name__ == "__main__":
    sys.exit(main())
