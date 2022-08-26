"""Wrapper for QSR MFG mode (calstate 1) commands"""
import re
import logging
from dataclasses import dataclass

from s4_connect import S4Connect
from utils import DEFAULT_ARMADA_IP, DEFAULT_QSR_IP


SEARCH_PARAMS = {
    "packets": r"(?:\[[0-9.]+ )?MPDU_GOOD = (\d+); MPDU_CRC = (\d+)",
    "rate": r"(?:\[[0-9.]+ )?MCS = (?P<mcs>\d+); RX_SYMBOL_NUM = (?P<rx_sym_num>\d+); "
    r"NSTS = (?P<nsts>\d+); BW = (?P<bandwidth>\d+); FORMAT = (?P<format>\d+)",
    "ru": r"(?:\[[0-9.]+ )?RU_Size = (?P<ru_size>\d+); RU_Indx = (?P<ru_index>\d+);  "
    r"SIGB_MCS = (?P<sigB_mcs>\d+);  GI_LTF = (?P<gi_ltf>\d+)",
    "he_ltf": r"(?:\[[0-9.]+ )?Num_SIGB = (?P<num_sigB>\d+); Num_HE_LTF = (?P<num_he_ltf>\d+); "
    r"STA_ID = (?P<sta_id>\d+);  TPE = (?P<TPE>\d+); A_fcator = (?P<a_factor>\d+); "
    r"Disambiguity = (?P<disambiguity>\d+)",
    "gain": r"(?:\[[0-9.]+ )?RX_GAIN = (?P<rx_gain>\d+); rgi = (?P<rgi>\d+); elna = (?P<elna>\d+)",
    "rssi": r"(?:\[[0-9.]+ )?RX_RSSI_dBm  : (-?\d+\.\d+), (-?\d+\.\d+), (-?\d+\.\d+), "
    r"(-?\d+\.\d+), (-?\d+\.\d+), (-?\d+\.\d+), (-?\d+\.\d+), (-?\d+\.\d+)",
    "evm": r"(?:\[[0-9.]+ )?EVM_AVG : (-?\d+\.\d+), ( ?-?\d+\.\d+), ( ?-?\d+\.\d+), ( ?-?\d+\.\d+)",
}


@dataclass
class TestModeConfig:
    """Configuration for set_test_mode"""

    channel: int = 114
    antenna_bitmask: int = 255
    mcs: int = 9
    bandwidth_mhz: int = 160
    packet_length: int = 40  # "packet size in 100bytes units"
    phy_format: int = 2  # (0=11/b/a/g, 1=11n, 2=11ac, 3=11ax)


class QsrMfg:
    """Class for QSR10G in MFG mode (calstate 1)"""

    def __init__(
        self,
        qsr_hostname: str = DEFAULT_QSR_IP,
        telnet_port: int = 23,
        server_hostname: str = DEFAULT_ARMADA_IP,
        autostart: bool = False,
    ):
        """Initialize the QsrDevice
        :param qsr_hostname: ip address for telnet
        :param telnet_port: port for telnet
        :param server_hostname: server (Dell/NUC) hostname
        :autostart: connect immediately or wait until sending command
        """
        self.logger = logging.getLogger(__name__)
        self.qsr = S4Connect(
            client_config={"hostname": qsr_hostname, "telnet_port": telnet_port},
            server_config={"hostname": server_hostname},
            autostart=autostart,
        )
        if self.qsr.get_calstate() != 1:
            raise RuntimeError("Not in calstate 1, exiting.")

    def get_temperature(self) -> float:
        """Get QT7810 (RFIC) temperature.
            Note: (QT10GU-AX (BBIC) temperature not supported in calstate 1)

        :return: RFIC temperature in C
        """
        resp = self.qsr.communicate_trig("call_qcsapi get_temperature")[0]
        rfic_temp_c = float(re.findall("\d+\.\d+", resp)[0])
        return rfic_temp_c

    def set_cal_modem(self, modem: int = 0):
        """Set modem (5GHz or 2.4 GHz)

        :param modem: 0 = 5 GHz, 2 = 2.4 GHz
        """
        if modem not in [0, 2]:
            raise IOError("Select valid modem from [0, 2]")
        return self.qsr.communicate_trig(f"set_cal_modem {modem}")

    def set_tx_pow(self, spi_id: int = 0, power_dbm: float = 13.0):
        """Set modem TX power with resolution of 0.1 dB
        Note: needs more experimentation to determine how this works.
        May be using LNA gain settings to set total power out?

        :param spi_id: modem antenna group {0|1|2}
            0 = antenna group 1
            1 = antenna group 2
            2 = 2.4 GHz antenna group 3
        :param power_dbm: desired output power in dBm
        """
        if spi_id not in [0, 1, 2]:
            raise IOError("Select valid spi_id from [0, 1, 2]")
        power_to_set = int(power_dbm * 10)
        return self.qsr.communicate_trig(f"set_tx_pow {spi_id} {power_to_set} 1")

    def set_test_mode(self, config: TestModeConfig = TestModeConfig):
        """Set the parameters to transmit

        :param config: TestModeConfig with parameters to set
        """
        self.stop_test_packet()
        # center_channel = int((config.channel - 2) + (config.bandwidth_mhz / 10))
        center_channel = config.channel
        cmd = (
            f"set_test_mode {center_channel} {config.antenna_bitmask} "
            f"{config.mcs} {config.bandwidth_mhz} {config.packet_length} "
            f"{config.phy_format}"
        )
        return self.qsr.communicate_trig(cmd)

    def send_test_packet(
        self,
        packet_count: int = 0,
        bandwidth: int = 99,
        mpdu_per_ampdu: int = 1,
        ppdu_mode: int = 0,
    ):
        """Transmit packets.

        :param packet_count: number of packets to transmit
            Note: default 0 transmits continuous
        :param bandwidth: bandwidth of packet to transmit
            Note: default 99 follows operation bandwidth from set_test_mode
        :param mpdu_per_ampdu: number of MPDU per AMPDU
        :param ppdu_mode: PPDU mode
            Note: only value 0 has been tested
        """
        trans_bw = {20: 0, 40: 1, 80: 2, 160: 3, 99: 99}

        if bandwidth not in trans_bw.keys():
            raise IOError(f"Invalid bandwidth {bandwidth}")
        if mpdu_per_ampdu < 1 or mpdu_per_ampdu > 64:
            raise IOError(f"Invalid MPDU per AMPDU {mpdu_per_ampdu}")
        if ppdu_mode not in [0, 2, 4]:
            raise IOError(f"Invalid PPDU Mode {ppdu_mode}")

        params = (
            f"{packet_count} {trans_bw[bandwidth]} {mpdu_per_ampdu - 1} {ppdu_mode}"
        )

        return self.qsr.communicate_trig(f"send_test_packet {params}")

    def stop_test_packet(self):
        """Stop transmitting packets"""
        return self.qsr.communicate_trig("stop_test_packet")

    def start_cw_signal(self, channel: int = 36):
        """Start transmitting CW signal. Warning: pretty sure it doesn't work

        :param channel: channel to transmit
        """
        self.stop_cw_signal()
        center_channel = int((channel - 2) + 16)
        return self.qsr.communicate_trig(f"send_cw_signal {center_channel} 0 0 0 0 1 1")

    def stop_cw_signal(self):
        """Stop transmitting CW signal"""
        return self.qsr.communicate_trig("stop_cw_signal")

    def show_test_packet(self, show: bool = False):
        """Parses show_test_packet

        :param show: print rx parameters to the command line
        """
        rx_params = {}
        # Clear dmesg to get output of only show_test_packet command
        self.qsr.communicate_trig("dmesg -c")
        raw_output = self.qsr.communicate_trig("show_test_packet 8; dmesg -c")[0]

        match_rx = re.search(SEARCH_PARAMS["packets"], raw_output)
        match_evm = re.search(SEARCH_PARAMS["evm"], raw_output)
        match_rssi = re.search(SEARCH_PARAMS["rssi"], raw_output)
        match_rate = re.search(SEARCH_PARAMS["rate"], raw_output)
        match_ru = re.search(SEARCH_PARAMS["ru"], raw_output)
        match_he = re.search(SEARCH_PARAMS["he_ltf"], raw_output)
        match_gain = re.search(SEARCH_PARAMS["gain"], raw_output)

        try:
            rx_params["rf_rx"] = [int(match_rx.group(i)) for i in [1, 2]]
        except (AttributeError, ValueError):
            self.logger.error("Could not parse RX packet numbers")
        try:
            rx_params["evm"] = [float(match_evm.group(i)) for i in range(1, 5)]
        except (AttributeError, ValueError):
            self.logger.error("Could not parse RX EVM")
        try:
            rx_params["rssi"] = [float(match_rssi.group(i)) for i in range(1, 9)]
        except (AttributeError, ValueError):
            self.logger.error("Could not parse RX RSSI")
        try:
            for key, value in match_rate.groupdict().items():
                if key == "bandwidth":
                    rx_params[key] = 20 * (2 ** int(value))
                else:
                    rx_params[key] = int(value)
            for key, value in match_ru.groupdict().items():
                rx_params[key] = int(value)
            for key, value in match_he.groupdict().items():
                rx_params[key] = int(value)
            for key, value in match_gain.groupdict().items():
                rx_params[key] = int(value)
        except (AttributeError, ValueError):
            self.logger.error("Could not parse additional RX parameters")

        if show:
            print("Full list of rx parameters: ")
            for key, value in rx_params.items():
                print("{}: {}".format(key, value))

        return rx_params
