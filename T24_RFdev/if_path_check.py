from titan24_prototypes.modules.lo import LO
from titan24_prototypes.modules.shf import SHF
from hw_qa_tools.fsw import SpectrumAnalyzer

fsw = SpectrumAnalyzer("10.13.23.78")
import pandas as pd
import numpy as np
import time


def main():

    trf = SHF()
    info = input("Polarization ? 0 for Vor 1 for H ")
    pol = int(info)  # horizontal
    # Parameters for testing

    lo_dsa = 10
    # Channel 0. Test the signal at Channel 0
    info = input("Path under test (0 1 2 3) ")
    path = int(info)
    fname = "output_if_tx_path_" + str(path) + ".xlsx"
    file_out = pd.ExcelWriter(fname)

    # Typical Tx attenuation
    if_tx_atten = 10
    trf.set_lo_attenuator(pol, lo_dsa)
    trf.set_rf_tx_attenuator(pol, path, if_tx_atten, True)
    # trf.rf_cpld.write_register(0 = RF_V,Reg = 3,Mode = 3,Read_Back = True)
    trf.write_rf_register(0, 3, 3, True)
    trf.set_mode("tx", [pol])
    results = []
    chain = [0, 1, 2, 3]
    for ch in chain:
        path = ch
        trf.set_rf_tx_attenuator(pol, path, if_tx_atten, True)
        trf.set_mode("rx", [pol])
        trf.set_mode("tx", [pol])
    # check path 0
    path = 1
    if_dsa = np.arange(0, 31.5, 0.5)
    for dsa in if_dsa:
        trf.set_rf_tx_attenuator(pol, path, dsa, True)
        trf.set_mode("rx", [pol])
        trf.set_mode("tx", [pol])
        data = fsw.get_peak(1)
        results.append(data[1])

        print("DSA atten = " + str(dsa) + " dB, peak power = " + str(data))
        time.sleep(1)

    # store data on file
    out_np = np.column_stack([if_dsa, results])
    out_df = pd.DataFrame(out_np, columns=["if_dsa", "output power"])
    sheet_name = "Path" + str(path)
    out_df.to_excel(file_out, sheet_name)
    file_out.save()


if __name__ == "__main__":
    main()
