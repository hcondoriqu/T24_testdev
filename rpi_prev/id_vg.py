import set_dac
import adc_read
import numpy as np
import pandas as pd


def init_dac():
    ch_v = ["ch0", "ch1", "ch2", "ch3"]
    for ch in ch_v:
        set_dac.set_dac(ch, 3)


def get_id_all():
    ch_v = ["ch0", "ch1", "ch2", "ch3"]
    out_data = []

    for ch in ch_v:
        out_data.append(adc_read.get_adc(ch) * 200)
    return out_data


def main():
    init_dac()

    ch_v = ["ch0", "ch1", "ch2", "ch3"]
    # get drain current vs gate voltage
    vdac_v = np.arange(3, 0.4, -0.001)
    file_out = pd.ExcelWriter("data_out.xlsx")
    print("sweep all channels")
    for ch in ch_v:
        print("sweep ", ch)
        id0 = []
        id1 = []
        id2 = []
        id3 = []
        vg = []
        for vdac in vdac_v:
            vg.append(-vdac - 2.5)
            set_dac.set_dac(ch, vdac)
            # get current readings:
            out_data = get_id_all()

            id0.append(out_data[0])
            id1.append(out_data[1])
            id2.append(out_data[2])
            id3.append(out_data[3])
            print("Drain current ", out_data)

        sheet_name = ch
        out_np = np.column_stack([vg, id0, id1, id2, id3])
        out_df = pd.DataFrame(
            out_np, columns=["Vg", "Id0 (mA)", "Id1 (mA)", "Id2 (mA)", "Id3 (mA)"]
        )
        out_df.to_excel(file_out, sheet_name)
        init_dac()

    file_out.save()


if __name__ == "__main__":
    main()
