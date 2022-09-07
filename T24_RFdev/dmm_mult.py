"""USB Visa Control for Rigol DMM"""
from __future__ import print_function

import argparse
import time
import pyvisa as visa
import sys

def parse_args():
    """Argument Parser for Command Line Control"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mode',
                        dest='mode',
                        choices=['DCV', 'ACV', 'DCI', 'ACI', 'CONT'],
                        help='Desired mode of the DMM')
    parser.add_argument('-a', '--auto',
                        dest='auto_meas_en',
                        choices=['ON', 'OFF'],
                        help='Sets auto measure ON or OFF')
    parser.add_argument('--gv',
                        dest='get_meas_val',
                        help='Returns the current measured value based on current value.',
                        action='store_true')
    parser.add_argument('--gr',
                        dest='get_range_val',
                        help='Returns the current measurement range value',
                        action='store_true')
    parser.add_argument('-r',
                        dest='reset_dmm',
                        help='Resets the DMM',
                        action='store_true')
    parser.add_argument('--sr',
                        dest='set_range_val',
                        choices=['0', '1', '2', '3', '4', '5'],
                        help='Sets the current measurement range')
    parser.add_argument('-v',
                        '--version',
                        dest='get_fw',
                        action='store_true',
                        help='Get firmware version for Rigol DMM')

    return parser.parse_args()


class Rigol():
    """"Class for Rigol DMM"""
    def __init__(self, address,mode):
        """Initialize class with info on Modes and Ranges Constants"""

        self.modes = {"DCV": "VOLTage:DC",
                      "ACV": "VOLTage:AC",
                      "DCI": "CURRent:DC",
                      "ACI": "CURRent:AC",
                      "CONT": "CONTinuity"}
        self.max_ranges = {"DCV": 4,
                           "ACV": 4,
                           "DCI": 5,
                           "ACI": 3,
                           "CONT": None}

        self.def_mode = "DCV"
        self.mode = mode
        if not self.mode:
            print("No Mode Specified, defaulting to DCV...")
            self.mode = self.def_mode

        r_m = visa.ResourceManager("@py")
        # devices = r_m.list_resources()
    
        self.device = r_m.open_resource(address)
        
    def get_firmware(self):
        """Return Rigol Firmware"""
        ident = self.device.query("*IDN?").split(',')
        return ident[3]

    def get_reading(self):
        """Return Mode Measurement"""
        return self.device.query(":MEASure:{}?".format(self.modes[self.mode]))

    def get_range(self):
        """Get Rigol Current Range Information"""
        return self.device.query(":MEASure:{}:RANGE?".format(self.modes[self.mode]))

    def set_range(self, range):
        """Set Rigol Range"""
        if self.max_ranges[self.mode] is None:
            raise RuntimeError('Current DMM mode does not have a RANGE value')
        if range < 0 or range > self.max_ranges[self.mode]:
            raise RuntimeError('Invalid DMM measurement range value')
        self.set_meas_mode("MANU")
        self.device.write(":MEASure:{} {}".format(self.modes[self.mode],range))
        return self.get_range()

    def get_mode(self):
        """Get current Mode of DMM"""
        resp = self.device.query(":FUNCtion?").strip()
        if resp not in self.modes.keys():
            print("Current DMM mode not supported. Defaulting DMM mode to DCV")
            resp = self.set_mode(self.def_mode)

        return resp

    def set_mode(self, mode):
        """Set DMM Mode"""
        self.device.query(":FUNCtion:{}".format(self.modes[mode]))
        resp = self.device.query(":FUNCtion?").strip()
        self.mode = resp

        return resp

    def is_self_test_passing(self):
        """Run Self Test"""
        self.device.write("*TST?")
        time.sleep(0.5)
        resp = int(self.device.read_until('\r', 0.5).strip())
        if resp == 0:
            print("DMM connection good. Self Test Passed")
            return True
        if resp == 1:
            print("DMM connection good. Self Test FAILED")
        else:
            print("Check DMM comm connection. Bad Response.")

        return False

    def set_meas_mode(self, meas_mode):
        """Set Measurement Mode Auto/Manual"""
        meas_modes = ["AUTO", "MANU"]
        if meas_mode in meas_modes:
            self.device.write(":MEASure {}".format(meas_mode))
        else:
            raise RuntimeError("Invalid Measure Mode: " + meas_mode)

        # to allow display to update, send a valid command...
        self.device.query("*IDN?")

        print("DMM Measure Mode set to " + meas_mode)

    def reset_dmm(self):
        """Reset DMM to device defaults"""
        self.device.write("*RST")
        print("DMM has been reset...")


def main():
    """Main Function for Command line compatibility"""
    args = parse_args()
    dmm = Rigol(args.mode)

    if args.auto_meas_en:
        if args.auto_meas_en == "ON":
            dmm.set_meas_mode("AUTO")
        elif args.auto_meas_en == "OFF":
            dmm.set_meas_mode("MANU")
        else:
            raise RuntimeError("Invalid DMM Auto Measurement setting")
    elif args.get_meas_val:
        print("Measured Value: {} {}".format(str(dmm.get_reading()), str(dmm.get_mode())))
    elif args.get_range_val:
        print("Range Value: " + str(dmm.get_range()))
    elif args.set_range_val:
        print("Range Value: " + str(dmm.set_range(int(args.set_range_val))))
    elif args.reset_dmm:
        dmm.reset_dmm()
    elif args.get_fw:
        print(dmm.get_firmware())

if __name__ == "__main__":
    main()