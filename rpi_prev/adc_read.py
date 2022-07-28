#! /usr/bin/env python
# I2C driver to get adc  data on T24 RF Boards

import smbus
import time
import sys
import math
import RPi.GPIO as GPIO


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
    return data_read


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
    # Debug step 1

    data_w = 0x0001
    write_data(data_w)
    data = get_data()
    print("ADC reading 0x000001" + " : " + str(data))

    # Debug step 2
    data_w = 0x010000
    write_data(data_w)
    data = get_data()
    print("ADC reading 0x010000" + " : " + str(data))


def main():

    get_adc()


if __name__ == "__main__":
    main()
