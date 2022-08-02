#! /usr/bin/env python
# I2C driver to get adc  data on T24 RF Boards

import smbus
import time
import sys
import math
import RPi.GPIO as GPIO
import pandas as pd
import numpy

bus = smbus.SMBus(1)  # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)


def get_data():
    """Gets reading data from the ADC

    Returns:
        bin array: Data read from the ADC
    """
    # Voltage conversion result register
    # the data in the ADC is store in address 0x01
    reg_sel = 0x1
    adc_i2c_address = 0x2F

    i2c_bus = smbus.SMBus(1)  # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)
    data_read = i2c_bus.read_word_data(adc_i2c_address, reg_sel)
    print("Data read binary: ", data_read)
    data_read2 = i2c_bus.read_i2c_block_data(adc_i2c_address, reg_sel)
    print("Data read binary: ", data_read2)
    data_read3 = [hex(h1) for h1 in data_read2]
    return data_read3


def write_data(data_w):
    """Writes into the command register on the ADC"""

    bus = smbus.SMBus(1)
    # For the 610-00298 0x2F is the ADC address
    adc_i2c_address = 0x2F
    # write into the command register
    register_address = 0x00
    # data to write
    # check 1

    bus.write_word_data(adc_i2c_address, register_address, data_w)


def get_adc():
    """
    Gets data from the ADC
    1. write into the command register the channel number to read from
    2. Read on the voltage conversion register Address = 0x01
    """
    p = np.arange(0, 16)
    # Debug step 1

    data_w = 0x020000
    write_data(data_w)
    data = get_data()
    print("ADC reading " + hex(data_w) + " : " + str(data))
    # Debug step 2

    for rs in p:
        # Debug step 3

        data_w = rs
        write_data(data_w)
        data = get_data()
        print("ADC reading" + hex(data_w) + " : " + str(data))

    # Debug step 4
    data_w = 0x040000
    write_data(data_w)
    data = get_data()
    print("ADC reading" + hex(data_w) + " : " + str(data))

    # Debug step 5

    data_w = 0x0008
    write_data(data_w)
    data = get_data()
    print("ADC reading" + hex(data_w) + " : " + str(data))

    # Debug step 6
    data_w = 0x080000
    write_data(data_w)
    data = get_data()
    print("ADC reading" + hex(data_w) + " : " + str(data))

    # Debug step 7
    data_w = 0xA000
    write_data(data_w)
    data = get_data()
    print("ADC reading" + hex(data_w) + " : " + str(data))


def main():

    get_adc()


if __name__ == "__main__":
    main()
