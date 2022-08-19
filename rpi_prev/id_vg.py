import set_dac
import adc_read
import numpy as np


def main():
    ch = 0
    # get drain current vs gate voltage
    vg = np.arange(3, 0.5, -0.1)
    for vdac in vg:
        set_dac.set_dac(ch, vdac)
        t = adc_read.get_adc(ch)
        t = t * 200
        print("Drain current ", t)
    set_dac.set_dac(ch, 3)


if __name__ == "__main__":
    main()
