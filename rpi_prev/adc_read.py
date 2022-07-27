#! /usr/bin/env python
# I2C driver to get temperature data on T24 RF Boards

import smbus
import time
import sys
import math
import RPi.GPIO as GPIO


bus = smbus.SMBus(1)  # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)


def get_adc():

    reg_sel = 0x1  # Voltage conversion result register
    adc_i2c_address = 0x2F
    i2c_bus = smbus.SMBus(1)  # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)
    data_read = i2c_bus.read_i2c_block_data(adc_i2c_address, reg_sel)
    print("Data read binary: ", data_read)
    data_msb = data_read[0]

    data_lsb = data_read[1]

    data_comb = data_msb | data_lsb
    adc_bin = data_comb

    return adc_bin


def write_reg(ch_dac):
    """Writes into the command register on the ADC"""

    bus = smbus.SMBus(1)
    # For the 610-00298 0x2F is the ADC address
    adc_i2c_address = 0x2F

    register_address = 0x0
    ## address pointing register
    data_1 = 0x0  ## points to the command register
    data_msb = 0x1  ## Ch0
    data_lsb = 0x0  ## configuration register
    data_array = [data_1, data_msb, data_lsb]
    bus.write_i2c_block_data(adc_i2c_address, register_address, data_array)


def get_data():
    # write into the command register the channel that we would need access
    ch_n = 0
    write_reg(ch_n)
    data = get_adc()
    print("ADC reading " + " : " + str(data))


def main():

    get_data()


if __name__ == "__main__":
    main()
