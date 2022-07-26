import smbus
import time
import sys
import math
import RPi.GPIO as GPIO


def set_dac(register, vdac):

    bus = smbus.SMBus(1)

    dac_address = int(0x4F)  # DAC address
    register_address = int(register)

    ## Check next 3 lines

    din_float = (4095 / 3.3) * vdac
    din_int = round(din_float)

    din_bin = bin(din_int)

    length = len(din_bin) - 2  # Remove 0b on 0bxxxxx

    if length < 5:
        Din_MSB = 0
        Din_LSB = din_int << 4

    else:
        Din_MSB = din_int >> 4
        Din_LSB = din_int & 0b0000000011111
        Din_LSB = Din_LSB << 4

    Din_array = [Din_MSB, Din_LSB]
    bus.write_i2c_block_data(dac_address, register_address, Din_array)


def main():
    ## Sets the DAC register 0 to 2 V

    vdac = 2
    for reg in [0, 1, 2, 3]:
        set_dac(reg, vdac)
        print("DAC  ch" + str(reg) + " set!")


if __name__ == "__main__":
    main()
