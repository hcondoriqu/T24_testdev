import tx_setup
from titan24_prototypes.modules.lo import LO
from titan24_prototypes.modules.shf import SHF
from titan24_prototypes.modules.mixer import Mixer
import pandas as pd
import numpy as np
import time

from hw_qa_tools.fsw import SpectrumAnalyzer


fsw = SpectrumAnalyzer("10.13.23.90")


def main():
    SN = input("SN?:")
    file_out = pd.ExcelWriter("bias_optim" + SN + ".xlsx")

    trf = SHF("192.168.100.1")
    tmix = Mixer("192.168.100.1")
    pol = input("Pol H 1 ,v 0?")
    shf_id = int(pol)
    info = input("path (0 1 2 3): ")
    path_test = int(info)
    lo_freq = float(input("LO frequency: [GHz] "))
    # sets the LO frequency in the synth
    tx_setup.set_lo(lo_freq)
    trf.set_mode("tx", [shf_id])

    vdacm = np.arange(0.7, 0.45, -0.005)  # normally 1,0.6

    t1 = input("Dac voltage? ")
    gate_dac = float(t1)

    mixer_atten2 = 0
    t1 = input("mixer_atten 1 ? ")
    mixer_atten1 = int(t1)
    t1 = input("if_atten")
    if_atten = int(t1)  # change to 15
    trf.set_mode("normal", [shf_id])
    input(
        "Connect the input signal on path: "
        + str(path_test)
        + "\npress enter when done"
    )
    for path in [path_test]:
        tx_setup.set_all_off(shf_id)
        tx_setup.tx_set_ch(shf_id, path, if_atten, mixer_atten1, mixer_atten2, gate_dac)
        time.sleep(1)

        vdac = []
        temp = []
        evm = []
        out_p = []
        id12 = []
        vg = []
        if_att_l = []

        # results = fsw.get_wlan_results()
        target_power = 19
        att_if = trf.get_rf_tx_attenuator(shf_id, path)
        for vd in vdacm:

            trf.set_rf_dac_voltage(shf_id, path, vd)
            time.sleep(2)

            t_ch = trf.get_rf_temperature(shf_id, path, "rf")
            temp.append(t_ch)
            id = trf.get_rf_adc_drain_current(shf_id, path)
            id12.append(id)
            vg.append(-vd - 2.5)
            vdac.append(vd)
            results = fsw.get_wlan_results()
            time.sleep(0.5)
            rms_pwr = results["avg rms power"]
            evm_meas = results["avg EVM all"]
            print("Settings before changing the IF DSA atten")
            print(vd, rms_pwr, evm_meas)
            atten_int = int(2 * (rms_pwr - target_power + att_if))
            new_atten = atten_int / 2
            if new_atten < 0:
                new_atten = 0

            print("Path to set the IF DSA attenuator: ", path)
            print("Set to new atten = ", new_atten)

            trf.set_rf_tx_attenuator(shf_id, path, new_atten, True)
            trf.set_mode("rx", [shf_id])
            time.sleep(0.4)
            trf.set_mode("tx", [shf_id])

            read_atten = trf.get_rf_tx_attenuator(shf_id, path)
            print("Read atten RF board = ", read_atten)

            time.sleep(0.5)
            results = fsw.get_wlan_results()

            rms_pwr2 = results["avg rms power"]
            evm_meas2 = results["avg EVM all"]

            evm.append(evm_meas2)
            out_p.append(rms_pwr2)
            if_att_l.append(new_atten)
            print("Settings after  adjusting the IF DSA atten to the target power")
            print(vd, rms_pwr2, evm_meas2)
            trf.set_rf_tx_attenuator(shf_id, path, att_if)

            trf.set_mode("rx", [shf_id])
            time.sleep(0.4)
            trf.set_mode("tx", [shf_id])

        trf.set_rf_dac_voltage(shf_id, path, 2.99)
        out_np = np.column_stack([vdac, out_p, evm, temp, id12, vg, if_att_l])
        out_df = pd.DataFrame(
            out_np, columns=["Vd12", "Power", "EVM", "temp", "Id12", "Vg", "if_atten"]
        )
        sheet_name = "Ch = " + str(path)
        out_df.to_excel(file_out, sheet_name)

    file_out.save()


if __name__ == "__main__":
    main()
