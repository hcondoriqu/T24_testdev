"""USB Visa Control for BK Precision Power Supply"""
from __future__ import print_function

import argparse
import pyvisa as visa
import sys

def parse_args():
    """Argument Parser for Command Line Control"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-t',
                        '--toggle',
                        dest='set_output',
                        choices=['ON','OFF'],
                        help='Toggle BK Precision output power.')
    parser.add_argument('-sv',
                        '--setvoltage',
                        dest='set_volt',
                        help='Sets output voltage value in Volts.')
    parser.add_argument('-sc',
                        '--setcurrent',
                        dest='set_curr',
                        help='Sets output current value in Amperes.')
    parser.add_argument('-so',
                        '--setovp',
                        dest='set_ovp',
                        help='Sets over voltage protection value.')
    parser.add_argument('-to',
                        '--toggleovp',
                        dest='toggle_ovp',
                        choices=['ON','OFF'],
                        help='Enable/disable over voltage protection.')
    parser.add_argument('-r',
                        '--read',
                        dest='read_vals',
                        action='store_true',
                        help='Returns output voltage and current.')
    parser.add_argument('-v',
                        '--version',
                        dest='get_fw',
                        action='store_true',
                        help='Get firmware version of BK Power Supply.')
    return parser.parse_args()


class BKPrecision():
    """Class for BK Precision Power Supply"""
    def __init__(self,address):
        """Initialize USB connection"""
        rm = visa.ResourceManager("@py")
        devices = rm.list_resources()
        visa_address = address
        self.device = rm.open_resource(visa_address)
        self.device.read_termination = '\n'
        self.device.write("SYST:REM")

    def toggle(self, state):
        """Toggles BK output power on/off"""
        self.device.write("OUTP {}".format(state))
        return self.get_values()

    def set_voltage(self, volts):
        """Set output voltage"""
        self.device.write("VOLT {}".format(volts))
        return self.get_values()

    def set_current(self, amps):
        """Set output current"""
        self.device.write("CURR {}".format(amps))
        return self.get_values()

    def set_protection(self, volts):
        """Set Over Voltage Protection"""
        self.device.write("VOLT:PROT {}".format(volts))
        return self.get_values()

    def toggle_protection(self, state):
        """Enables or disables over voltage protection"""
        self.device.write("VOLT:PROT:STAT {}".format(state))
        return self.get_values()

    def get_values(self):
        """Returns the settings and readings from the BK Power Supply
            Must be a separate method to avoid pyvisa timeout errors
            """
        meas = []
        meas.append(self.device.query("VOLT?"))
        meas.append(self.device.query("MEAS:VOLT?"))
        meas.append(self.device.query("CURR?"))
        meas.append(self.device.query("MEAS:CURR?"))
        meas.append(self.device.query("VOLT:PROT?"))
        output = self.device.query("OUTP?")
        if output == "1":
            meas.append("ON")
        elif output == "0":
            meas.append("OFF")
        return meas

    def get_firmware(self):
        """Return BK Power Supply Firmware"""
        ident = self.device.query("*IDN?").split(", ")
        return ident[3]

def main():
    """Main Function for Command line compatibility"""
    args = parse_args()
    bkp = BKPrecision()
    if args.set_output:
        print("Power Supply Output State is {}"\
            .format(bkp.toggle(args.set_output)[5]))
    if args.set_volt:
        values = bkp.set_voltage(args.set_volt)
        print("Output voltage set to {}V"\
            .format(bkp.set_voltage(args.set_volt)[0]))
    if args.set_curr:
        values = bkp.set_current(args.set_curr)
        print("Output current set to {}A"\
            .format(bkp.set_current(args.set_curr)[2]))
    if args.set_ovp:
        print("Over Voltage Protection set to {}V"\
            .format(bkp.set_protection(args.set_ovp)[4]))
    if args.toggle_ovp:
        print("Over voltage protection is set to {}V"\
            .format(bkp.toggle_protection(args.toggle_ovp)[4]))
    if args.read_vals:
        values = bkp.get_values()
        print("Output voltage set to: {}V".format(values[0]))
        print("Actual output voltage: {}V".format(values[1]))
        print("Output current set to: {}A".format(values[2]))
        print("Actual output current: {}A".format(values[3]))
    if args.get_fw:
        print("BK Precision Power Supply Firmware Version: " \
            + bkp.get_firmware())

if __name__ == "__main__":
    main()
