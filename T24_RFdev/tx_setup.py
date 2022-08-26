import lo
import shf
import mixer
import time
import qsr_mfg
import time


def tx_set_ch(
    shf_id: int,
    path: int,
    if_atten_db: float = 10,
    mixer_atten1: int = 10,
    mixer_atten2: int = 0,
    gate_dac: float = 0.8,
):

    trf = shf.SHF("192.168.100.1")
    tmix = mixer.Mixer("192.168.100.1")

    # set the modem to send packets
    tmod = qsr_mfg.QsrMfg()
    tmod.set_test_mode()
    tmod.send_test_packet()

    # set the LO DSA in the given path
    # 10 db works for most of the frequencies/paths
    # might need to be individually adjusted for each case
    trf.set_lo_attenuator(shf_id, 10)

    # Set IF DSA on the RF board.
    # print("IF attenuation = ", if_atten_db)
    trf.set_rf_tx_attenuator(shf_id, path, if_atten_db)

    # mixer
    tmix.enable_mixer(shf_id, path)
    tmix.set_tx_attenuator1(shf_id, path, mixer_atten1)
    tmix.set_tx_attenuator2(shf_id, path, mixer_atten2)
    trf.set_mode("rx", [shf_id])
    time.sleep(0.4)
    trf.set_mode("tx", [shf_id])

    # fem bias
    trf.set_rf_dac_voltage(shf_id, path, gate_dac)


def get_pd_cw(shf_id, path):
    trf = shf.SHF("192.168.100.1")
    # trf.if_cpld.write_register(5,0,True)
    r = trf.get_rf_sim_adc_voltages(shf_id, path, True)
    # print("power det ", r)

    if_av = r.if_vdet
    rf0_av = r.rf_0
    rf1_av = r.rf_1
    return [if_av, rf0_av, rf1_av]


def set_lo(lo_freq, lo_dsa=10):
    # sets the frequency on the synth
    # sets the attenuation on the LO distribution
    # in the RF board
    tlo = lo.LO("192.168.100.1")
    tlo.set_frequency_ghz(lo_freq)
    return None


def set_all_off(shf_id):
    # turns off all paths
    #
    # disables IF bgus
    # disables mixer
    # Set the gate to -5 V
    # all DSA for max values
    trf = shf.SHF("192.168.100.1")
    tmix = mixer.Mixer("192.168.100.1")

    # set the modem to stop sending packets
    tmod = qsr_mfg.QsrMfg()
    tmod.set_test_mode()

    # set LO DSA to 31 dB
    trf.set_lo_attenuator(shf_id, 31)
    for path in [0, 1, 2, 3]:
        # Set IF DSA on the RF board.
        trf.set_rf_tx_attenuator(shf_id, path, 31.5)

        # mixer
        tmix.disable_mixer(shf_id, path)
        tmix.set_tx_attenuator1(shf_id, path, 15)
        tmix.set_tx_attenuator2(shf_id, path, 15)
        trf.set_mode("rx", [shf_id])
        time.sleep(0.4)
        trf.set_mode("tx", [shf_id])

        # fem bias
        trf.set_rf_dac_voltage(shf_id, path, 2.99)

    print("all paths are turned off")


def main():
    # input set  parameters
    shf_id = input("Pol: 0 (V) and 1 (H) ")
    shf_id = int(shf_id)
    path_id = input("Path id [0,1,2,3] or off ")

    if path_id in ["0", "1", "2", "3"]:
        path_id = int(path_id)
        print("setting up path: ", path_id)
        lo_freq = float(input("LO frequency: [GHz] "))
        # sets the LO frequency in the synth
        set_lo(lo_freq)
        tx_set_ch(shf_id, path_id)

    if path_id == "off":
        set_all_off(shf_id)


if __name__ == "__main__":
    main()
