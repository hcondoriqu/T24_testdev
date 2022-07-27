#! /usr/bin/env python
# I2C driver to get temperature data on T24 RF Boards

import smbus
import time
import sys
import math
import RPi.GPIO as GPIO


bus = smbus.SMBus(1)  # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)


def get_adc(reg):

    reg_sel = reg  # ADC Register
    adc_i2c_address = 0x2F
    i2c_bus = smbus.SMBus(1)  # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)

    reg_sel = 0x00  # Temperature Register

    data_read = i2c_bus.read_i2c_block_data(adc_i2c_address, reg_sel)
    data_msb = data_read[0] << 8
    data_lsb = data_read[1]
    data_comb = data_msb | data_lsb
    adc_bin = data_comb >> 5  # change to 11bit

    # check negative temp bit status
    neg_data_check = adc_bin & 0b10000000000
    neg_bit_check = neg_data_check >> 10

    if neg_bit_check == 0:
        adc_read = adc_bin * 0.125
        # print ("Temp degC: ", temp_read)

    else:
        adc_read = adc_bin ^ 0b11111111111
        adc_read = adc_read + 1
        adc_read = adc_read * -0.125
        # print ("Qorvo1 Temp degC: -", temp_read)

    return adc_read


def get_data(reg):
    data = get_adc(reg)
    print("ADC reading " + str(reg) + " : " + str(data))


def main():
    reg_map = [1, 2, 3, 4, 5, 6, 7, 8]
    for reg in reg_map:
        get_data(reg)


if __name__ == "__main__":
    main()
