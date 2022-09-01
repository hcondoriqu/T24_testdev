import pyvisa as visa
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def get_data_fsw():
    rm = visa.ResourceManager("@py")
    # Initiates the conexion to the FSW
    FSW = rm.open_resource("TCPIP::10.13.23.90::INSTR")

    # Scale the CCDF plot:
    # Defines a power level range of 20 dB mean pwr for the x-axis
    FSW.write("CALC:STAT:SCAL:X:RANG 20dB")
    # Displays percentage values on y-axis scale
    FSW.write("CALC:STAT:SCAL:Y:UNIT PCT")
    # sets the mode to continuous off
    FSW.write("INIT:CONT OFF")
    # Sets the markers
    # Sets marker 1 to the 0.1% probability value.
    # FSW.write("CALC:MARK1:Y:PERC 0.1PCT")
    # Gets the CCDF trace
    traceASC = FSW.query_ascii_values("FORM ASC;:TRAC? TRACE1")
    data = np.array(traceASC)

    # If required to enable multiple measurements set n>1
    n = 1
    for ind in np.arange(1, n):
        FSW.write("INIT:CONT ON")
        print("getting data # ", ind)
        time.sleep(1)
        traceASC = FSW.query_ascii_values("FORM ASC;:TRAC? TRACE1")
        FSW.write("INIT:CONT OFF")
        data = np.c_[data, traceASC]

    # get Mean power, peak, and crest factor
    ccdf_mean = FSW.query_ascii_values("CALC:STAT:RES1? MEAN")
    ccdf_peak = FSW.query_ascii_values("CALC:STAT:RES1? PEAK")
    ccdf_crest = FSW.query_ascii_values("CALC:STAT:RES1? CFACTOR")
    ccdf_summary = {
        "Average RMS Power (dBm)": ccdf_mean,
        "Peak power (dBm)": ccdf_peak,
        "Crest Factor (dB)": ccdf_crest,
    }
    FSW.write("INIT:CONT ON")

    return data, ccdf_summary


def plot_data(power, data, file_name, ccdf_summary):
    plt.semilogy(power, data)
    plt.xlabel("PAPR (dB)")
    plt.ylabel("CCDF(%)")
    plt.xlim([0, 15])
    plt.grid(True, linestyle="--")
    rms_p = ccdf_summary["Average RMS Power (dBm)"]
    peak_p = ccdf_summary["Peak power (dBm)"]
    cr_fc = ccdf_summary["Crest Factor (dB)"]
    t_mean = "Avg Pwr (dBm): " + "{:.2f}".format(rms_p[0])
    t_peak = "Peak pwr (dBm): " + "{:.2f}".format(peak_p[0])
    t_cf = "Crest Fact (dB): " + "{:.2f}".format(cr_fc[0])
    text2 = t_mean + "\n" + t_peak + "\n" + t_cf
    plt.text(10.1, 1.5, text2, fontsize=8)
    plt.savefig(file_name + "_plot.png", dpi=300)


def get_ccdf():
    note = "\n\nThis method assumes that: \nThe FSW is on CCDF mode\n\n "
    print(note)
    file_name = input("file name to save the data ")
    fname = file_name + ".xlsx"
    file_out = pd.ExcelWriter(fname)
    traceASC, ccdf_summary = get_data_fsw()
    power = np.linspace(0, 20, 1001)
    plot_data(power, traceASC, file_name, ccdf_summary)
    out_np = np.column_stack([power, traceASC])
    out_df = pd.DataFrame(out_np)
    sheet_name = "CCDF"
    out_df.to_excel(file_out, sheet_name)
    df2 = pd.DataFrame(data=ccdf_summary, index=[0])
    df2 = df2.T
    df2.to_excel(file_out, "CCDF summary")
    file_out.save()


def main():
    get_ccdf()


if __name__ == "__main__":
    main()
