import smbus
import time
import sys
import math
import RPi.GPIO as GPIO


def set_dac(ch_dac, vdac):
    ch_map = {"ch0": 0x10, "ch1": 0x12, "ch2": 0x14, "ch3": 0x16}
    bus = smbus.SMBus(1)

    dac_address = int(0x4F)  # DAC address
    register_address = int(ch_map[ch_dac])

    ## Check next 3 lines

    din_float = (4095 / 3.3) * vdac
    din_int = round(din_float)

    din_bin = bin(din_int)

    length = len(din_bin) - 2  # Remove 0b on 0bxxxxx

    if length < 5:
        data_msb = 0
        data_lsb = din_int << 4

    else:
        data_msb = din_int >> 4
        data_lsb = din_int & 0b0000000011111
        data_lsb = data_lsb << 4

    data_array = [data_msb, data_lsb]
    bus.write_i2c_block_data(dac_address, register_address, data_array)
    return None


def main():
    # Sets all DAC channels to  2 V
    channels = ["ch0", "ch1", "ch2", "ch3"]
    vdac = 2
    for ch_dac in channels:
        set_dac(ch_dac, vdac)
        print("DAC " + ch_dac + " set!")
    return None


if __name__ == "__main__":
    main()
