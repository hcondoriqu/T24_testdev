#! /usr/bin/env python
# I2C driver to get temperature data on T24 RF Boards

import smbus
import time
import sys
import math
import RPi.GPIO as GPIO


bus = smbus.SMBus(1)  # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)


def get_adc():

    Reg_SEL = 0x00  # ADC Register
    adc_i2c_address = 0x2F
    bus = smbus.SMBus(1)  # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)

    Reg_SEL = 0x00  # Temperature Register

    Data_read = bus.read_i2c_block_data(adc_i2c_address, Reg_SEL)
    Data_MSB = Data_read[0] << 8
    Data_LSB = Data_read[1]
    Data_comb = Data_MSB | Data_LSB
    adc_bin = Data_comb >> 5  # change to 11bit

    # check negative temp bit status
    Neg_data_check = adc_bin & 0b10000000000
    Neg_bit_check = Neg_data_check >> 10

    if Neg_bit_check == 0:
        adc_read = adc_bin * 0.125
        # print ("Temp degC: ", temp_read)

    else:
        adc_read = adc_bin ^ 0b11111111111
        adc_read = adc_read + 1
        adc_read = adc_read * -0.125
        # print ("Qorvo1 Temp degC: -", temp_read)

    return adc_read


def get_data():
    data = get_adc()
    print("ADC reading " + " : " + str(data))


def main():
    get_data()


if __name__ == "__main__":
    main()
