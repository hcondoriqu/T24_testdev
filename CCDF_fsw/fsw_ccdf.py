import pyvisa as visa
import time
import pandas as pd
import numpy as np


def get_ccdf():
    note = "This method assumes that: \nThe FSW is on CCDF mode \nThere is a CCDF curve is already measured"
    print(note)
    file_name = input("file name to save the data ")
    fname = file_name + ".xlsx"
    file_out = pd.ExcelWriter(fname)
    rm = visa.ResourceManager("@py")
    FSW = rm.open_resource("TCPIP::10.13.23.90::INSTR")
    print("Fetching trace in ASCII format... ")
    traceASC = FSW.query_ascii_values("FORM ASC;:TRAC? TRACE1")
    out_np = np.column_stack(traceASC)
    out_df = pd.DataFrame(out_np)
    sheet_name = "CCDF"
    out_df.to_excel(file_out, sheet_name)
    file_out.save()


def main():
    get_ccdf()


if __name__ == "__main__":
    main()
