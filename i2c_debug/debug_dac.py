import smbus
import time
import sys
import math
import RPi.GPIO as GPIO
import os


def set_dac(ch_dac, vdac):
    """Sets the DAC 7574 on the RF board

    Args:
        ch_dac (string): DAC Channel
        vdac (float): DAC value to set in ch_dac

    Returns:
        None
    """
    set_i2c_back()
    ch_map = {"ch0": 0x10, "ch1": 0x12, "ch2": 0x14, "ch3": 0x16}
    bus = smbus.SMBus(1)
    # For the 610-00298 0x4F is the DAC address
    dac_address = int(0x4F)  # DAC address
    register_address = int(ch_map[ch_dac])
    # Converts the vdac variable to hexadecimal
    # The data has 12 bits total D[11:0]
    # first eight bits: D[11:4] sent on MSB [7:0]
    # last four bits  : D[3:0]  sent on LSB[7:4]
    # LSB[3:0] is filled with ceros
    din_float = (4095 / 3) * vdac
    din_int = round(din_float)
    din_bin = bin(din_int)
    length = len(din_bin) - 2  # Remove 0b on 0bxxxxx
    # if data binary requires only 4 bits
    if length < 5:
        data_msb = 0
        data_lsb = din_int << 4

    else:
        data_msb = din_int >> 4
        data_lsb = din_int & 0b000000011111
        data_lsb = data_lsb << 4

    data_array = [data_msb, data_lsb]
    bus.write_i2c_block_data(dac_address, register_address, data_array)


def set_i2c_back():
    bashCommand = "gpio -g mode 2 alt0"
    os.system(bashCommand)
    bashCommand = "gpio -g mode 3 alt0"
    os.system(bashCommand)
    return None


def main():
    """Test the set_dac method
    Sets all channels on the DAC 7574 to 2V

    Returns:
    None
    """
    # Sets all DAC channels to  2 V
    channels = ["ch0", "ch1", "ch2", "ch3"]
    vdac = 2
    for ch_dac in channels:
        set_dac(ch_dac, vdac)
        print("DAC " + ch_dac + " set!")


if __name__ == "__main__":
    main()
