import pyvisa as visa
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def get_data_fsw():
    rm = visa.ResourceManager("@py")
    # Initiates the conexion to the FSW
    FSW = rm.open_resource("TCPIP::10.13.23.90::INSTR")

    FSW.write("INIT:CONT OFF")
    # Sets the markers
    # Sets marker 1 to the 0.1% probability value.
    #

    print("Fetching trace in ASCII format... ")
    traceASC = FSW.query_ascii_values("FORM ASC;:TRAC? TRACE1")
    data = np.array(traceASC)
    return data


def plot_data(data, power):
    plt.semilogy(power, data)
    plt.show()


def get_ccdf():
    note = "This method assumes that: \nThe FSW is on CCDF mode \nThere is a CCDF curve is already measured"

    data = get_data_fsw()
    power = np.linspace(1e-6, 20, 1001)


def main():
    get_ccdf()


if __name__ == "__main__":
    main()
