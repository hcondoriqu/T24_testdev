#! /usr/bin/env python
# Author: Dan Pond
# script for accessing FPGA registers over SPI bus.
# requires Titan RF  adapter board
# this script has some limitations:
# arguments are interpreted as hexadecimal (and converted to integer for
# use inside this script)
# all printed values are hexadecimal.
# There is no protection against multiple sessions using the same GPIOs.


import sys
import math
import time
import sys
import RPi.GPIO as GPIO

usage = "Usage: \n t_rw.py <peek|poke> address [write_value]\n"


SPI_SS_PIN = 24
SPI_SCLK_PIN = 23
SPI_MOSI_PIN = 19
SPI_MISO_PIN = 21


# Note: internally values shall be passed integers (decimal).




def main():
  if len(sys.argv) < 3 or len(sys.argv) > 4:
    sys.exit(usage)

  address = int(sys.argv[2],16) # Always hex input, convert to int
  address = address << 1        # shift address to make room for read bit

  spi_init()

  if (sys.argv[1] == "peek"):
    address |= 1        # Set read bit
    spi_peek(address)

  elif (sys.argv[1] == "poke"):
    write_value = int(sys.argv[3],16) # Always hex input, convert to int
    spi_poke(address, write_value)


  else:
    sys.exit(usage)

  sys.exit()


def spi_init():
  GPIO.setmode(GPIO.BOARD)
  GPIO.setwarnings(False)
  GPIO.setup([SPI_SS_PIN, SPI_SCLK_PIN, SPI_MOSI_PIN], GPIO.OUT)
  GPIO.setup([SPI_MISO_PIN], GPIO.IN)
  GPIO.output(SPI_SS_PIN, GPIO.HIGH)
  GPIO.output(SPI_SCLK_PIN, GPIO.LOW)
  GPIO.output(SPI_MOSI_PIN, GPIO.LOW)


def spi_peek(address):
  # send address (8 bits)
  # capture 16-bit read value

  GPIO.output(SPI_SS_PIN, 0)
  GPIO.output(SPI_SCLK_PIN, 0)

  send_byte(address)
  data = read16()

  GPIO.output(SPI_SS_PIN, 1)
  address = address >> 1
  #print "debug:{}".format(data)
  print ("FPGA READ A:0x{:02x} D:0x{:04x}".format(address, data))



def spi_poke(address,write_value):
  # send address (8 bits)
  upper = write_value >> 8
  lower = write_value & 255

  GPIO.output(SPI_SS_PIN, 0)
  GPIO.output(SPI_SCLK_PIN, 0)

  for i in (address,upper,lower):
    send_byte(i)

  GPIO.output(SPI_SS_PIN, 1)
  address = address >> 1

  print ("FPGA WRITE A:0x{:02x} D:0x{:04x}".format(address,write_value))

def send_byte(value):

  # value is assumed to be decimal string
  # need to convert to binary list
  data = list("{0:08b}".format(value))

  for bits in data:
    GPIO.output(SPI_MOSI_PIN, int(bits)) # express data bit
    GPIO.output(SPI_SCLK_PIN, GPIO.HIGH) # clock high
    GPIO.output(SPI_SCLK_PIN, GPIO.LOW)  # clock low


def read16():
  GPIO.output(SPI_SCLK_PIN, 0)
  data = []

  for _ in range(16):
    data.append(GPIO.input(SPI_MISO_PIN))
    GPIO.output(SPI_SCLK_PIN, 1)
    GPIO.output(SPI_SCLK_PIN, 0)

  read_data = int("".join(map(str,data)),2)
  #print "read_data={}".format(read_data)

  return read_data

  # Fix




if __name__ == '__main__':
   sys.exit(main())

