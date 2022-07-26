#! /usr/bin/env python
# I2C driver to get adc  data on T24 RF Boards

import smbus
import time
import sys
import math
import RPi.GPIO as GPIO
import pandas as pd
import numpy as np

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

    data_read = bus.read_i2c_block_data(adc_i2c_address, reg_sel, 2)  # read 2 bytes
    data_v = (data_read[0] & 0b00001111) * 256 + data_read[1]
    # This data needs to be normalized to 2.5V/4096
    data_v = data_v * 2.5 / 4096
    return data_v


def write_data(ch):
    """Writes into the command register on the ADC"""
    ch_map = {"ch0": 0x80, "ch1": 0x40, "ch2": 0x20, "ch3": 0x10}
    bus = smbus.SMBus(1)
    # For the 610-00298 0x2F is the ADC address
    adc_i2c_address = 0x2F
    # write into the command register
    register_address = 0x00
    # data to write
    # check 1

    bus.write_word_data(adc_i2c_address, register_address, ch_map[ch])


def get_adc(ch):
    """
    Gets data from the ADC
    1. write into the command register the channel number to read from
    2. Read on the voltage conversion register Address = 0x01
    """
    write_data(ch)
    data = get_data()
    return data


def main():
    ch_v = [
        "ch0",
        "ch1",
        "ch2",
        "ch3",
    ]
    for ch in ch_v:
        data_read = get_adc(ch)
        print("data from adc on ch " + str(ch) + " : " + str(data_read))


if __name__ == "__main__":
    main()
