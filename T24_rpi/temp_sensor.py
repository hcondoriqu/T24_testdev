#! /usr/bin/env python
# I2C driver to get temperature data on T24 RF Boards

import smbus
import time
import sys
import math
import RPi.GPIO as GPIO


bus = smbus.SMBus(1)  # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)


def get_temp(ch):

    Reg_SEL = 0x00  # Temperature Register
    chan_map = {"ch0": 0x49, "ch1": 0x4C, "ch2": 0x4D, "ch3": 0x4A}
    bus = smbus.SMBus(1)  # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)

    Reg_SEL = 0x00  # Temperature Register

    TempSen_address = chan_map[ch]

    Data_read = bus.read_i2c_block_data(TempSen_address, Reg_SEL)
    Data_MSB = Data_read[0] << 8
    Data_LSB = Data_read[1]
    Data_comb = Data_MSB | Data_LSB
    Temp_bin = Data_comb >> 5  # change to 11bit

    # check negative temp bit status
    Neg_data_check = Temp_bin & 0b10000000000
    Neg_bit_check = Neg_data_check >> 10

    if Neg_bit_check == 0:
        temp_read = Temp_bin * 0.125
        # print ("Temp degC: ", temp_read)

    else:
        temp_read = Temp_bin ^ 0b11111111111
        temp_read = temp_read + 1
        temp_read = temp_read * -0.125
        # print ("Qorvo1 Temp degC: -", temp_read)

    return temp_read


def get_data():
    channels = ["ch0", "ch1", "ch2", "ch3"]
    for ch in channels:
        temp = get_temp(ch)
        print("Temp degC " + ch + " : " + str(temp))
    return None


def main():
    get_data()


if __name__ == "__main__":
    main()
