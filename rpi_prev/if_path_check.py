import t24_rf
from hw_qa_tools.fsw import SpectrumAnalyzer
fsw = SpectrumAnalyzer('10.13.23.69')
import pandas as pd
import numpy as np
def main():

    file_out = pd.ExcelWriter('output_if_rpi.xlsx')

    trf = t24_rf.SHF("rf")
    pol = 0 # Vertical
    # Parameters for testing
    
    lo_dsa = 10
    # Channel 0. Test the signal at Channel 0
    path = 0 
    # Typical Tx attenuation
    if_tx_atten = 0
    trf.set_lo_attenuator(pol,lo_dsa)  
    trf.set_rf_tx_attenuator(pol,path,if_tx_atten)
    # trf.rf_cpld.write_register(0 = RF_V,Reg = 3,Mode = 3,Read_Back = True)
    trf.rf_cpld.write_register(0,3,3,True)
    trf.set_mode("tx", [0]])
    results = []
    chain = [0,1,2,3]
    for ch in chain:
        path =ch
        trf.set_rf_tx_attenuator(pol,path,if_tx_atten)
        trf.set_mode("rx", [0])
        trf.set_mode("tx", [0])
    # check path 0
    path = 0;
    if_dsa = np.arange(0,31.5,0.5)
    for dsa in if_dsa:
        trf.set_rf_tx_attenuator(pol,path,dsa)
        trf.set_mode("rx", [0])
        trf.set_mode("tx", [0])
        data = fsw.get_peak()
        results.append(data)
        

    # store data on file
    out_np   = np.column_stack([if_dsa,results])
    out_df   = pd.DataFrame(out_np, columns = ["if_dsa",'output power'])
    sheet_name = "DSA_ch0"
    out_df.to_excel(file_out,sheet_name)



    
if __name__ == "__main__":
    main()
