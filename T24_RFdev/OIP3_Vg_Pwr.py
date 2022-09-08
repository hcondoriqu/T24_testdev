from calendar import prweek
import pandas as pd
import numpy as np
import dmm_mult
import bk_mult
import time
from hw_qa_tools.fsw import SpectrumAnalyzer
from hw_qa_tools import visa_generator as SG

fsw = SpectrumAnalyzer("10.13.35.219")
MXG1 = SG.SignalGenerator("10.13.23.77")
MXG2 = SG.SignalGenerator("10.13.23.78")
# MXG2 = SG.visa_generator("10.13.23.219")


# enable bk and dmm
vg12_bk = bk_mult.BKPrecision("USB0::65535::37376::802204020757310056::0::INSTR")
vg3_bk = bk_mult.BKPrecision("USB0::65535::37376::802204020757710016::0::INSTR")
# dmm_mult allows multiple Rigol DMM to be instantiated.
dmm3 = dmm_mult.Rigol("USB0::6833::2500::DM3R221300366::0::INSTR", "DCI")
dmm12 = dmm_mult.Rigol("USB0::6833::2500::DM3R184250156::0::INSTR", "DCI")


freq_rf = 24.35  # 5.57


def main():
    SN = input("Save file as: ")
    file_out = pd.ExcelWriter(SN + "2tone_OIP3.xlsx")
    info = input("tone_separation MHz ( 10 20 80):")
    tone_sep = int(info)
    frf_out = freq_rf * 1e9
    # info = input("Power level MXG : (-10,-5, 0) ")
    # initial power level
    pwr_level = -10
    fsw.set_frequency(frf_out)
    fsw.set_span(1e9)
    time.sleep(1)
    MXG1.set_amplitude(pwr_level)
    MXG2.set_amplitude(pwr_level)

    print("Offset MHz: ", tone_sep)
    fr1 = freq_rf * 1e9 - 1e6 * tone_sep / 2
    fr2 = freq_rf * 1e9 + 1e6 * tone_sep / 2
    # Test for OIP3 at the output of the RF board:
    # Synth = 9.39 GHz.

    fr1_out = freq_rf * 1e9 - 1e6 * tone_sep / 2  # +9.39e9*2
    fr2_out = freq_rf * 1e9 + 1e6 * tone_sep / 2  # +9.39e9*2
    MXG1.set_frequency(fr1_out)
    MXG2.set_frequency(fr2_out)

    p1_m = []
    p2_m = []
    im1_m = []
    im2_m = []
    fsw.set_span(tone_sep * 1e7)
    time.sleep(1)
    MXG1.on()
    MXG2.on()

    # Equalize both tones:
    pout_2 = pwr_level
    pout_1 = pout_2
    MXG1.set_amplitude(pout_1 + 0)  # Loss factor was 10.5 before
    MXG2.set_amplitude(pout_2 + 0)  # Loss facor was 10.7 before

    fsw.set_marker(1, fr1_out)
    fsw.set_marker(2, fr2_out)
    fsw.set_marker(3, 2 * fr1_out - fr2_out)
    fsw.set_marker(4, 2 * fr2_out - fr1_out)
    time.sleep(0.2)

    vg12_range = np.arange(2.3, 1.8, -0.05)
    vg3_range = np.arange(2.45, 2.1, -0.05)
    Inpwr_level = np.arang(-25, 6, 1)
    for pwr_level in Inpwr_level:
        # Equalize both tones:
        pout_2 = pwr_level
        pout_1 = pout_2
        MXG1.set_amplitude(pout_1 + 0)  # Loss factor was 10.5 before
        MXG2.set_amplitude(pout_2 + 0)  # Loss facor was 10.7 before
        # initialize and wait for the PA to stabilize
        vg12_bk.set_voltage(vg12_range[0])
        vg3_bk.set_voltage(vg3_range[0])
        time.sleep(2)

        pwr_tone1_m = []
        pwr_tone2_m = []
        pwr_im1_m = []
        pwr_im2_m = []
        id_out_m12 = []
        id_out_m3 = []
        pwr_tone1 = []
        pwr_tone2 = []
        pwr_im1 = []
        pwr_im2 = []

        id_out_v12 = []
        id_out_v3 = []
        vg3_v = []
        vg12_v = []
        pwrl_v = []
        for vg3 in vg3_range:

            # set Gate voltage
            vg3_bk.set_voltage(vg3)
            vg12_bk.set_voltage(vg12_range[0])
            for vg12 in vg12_range:
                vg12_bk.set_voltage(vg12)
                read_power = fsw.get_power(1)
                pwr_tone1.append(read_power)
                read_power = fsw.get_power(2)
                pwr_tone2.append(read_power)
                read_power = fsw.get_power(3)
                pwr_im1.append(read_power)
                read_power = fsw.get_power(4)
                pwr_im2.append(read_power)
                # Get ID12 under drive
                i_read = dmm12.get_reading()
                i_read = round(float(i_read) * 1000, 2)
                id_out_v12.append(i_read)

                # Get ID3 under drive
                i_read3 = dmm3.get_reading()
                i_read3 = round(abs(float(i_read3) * 1000), 2)
                id_out_v3.append(i_read3)
                vg3_v.append(vg3)
                vg12_v.append(vg12)
                pwrl_v.append(pwr_level)

        out_np = np.column_stack(
            [
                pwrl_v,
                vg12_v,
                vg3_v,
                id_out_v12,
                id_out_v3,
                pwr_tone1,
                pwr_tone2,
                pwr_im1,
                pwr_im2,
            ]
        )
        out_df = pd.DataFrame(
            out_np,
            columns=[
                "Input power level (dBm)",
                "vg12 (V)",
                "vg3 (V)",
                "id12 (mA)",
                "id3_m (mA)",
                "Tone 1 (dBm)",
                "Tone 2 (dBm)",
                "IM 1 (dBm)",
                "IM2 (dBm)",
            ],
        )

        sheet_name = "Input Power = " + str(round(pwr_level, 3))
        out_df.to_excel(file_out, sheet_name)

    MXG1.off()
    MXG2.off()
    file_out.save()


if __name__ == "__main__":
    main()
