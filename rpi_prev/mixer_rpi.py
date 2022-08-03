import admv_r_w
import time

STARRY_DEFAULTS = {
    0x0000: 0x00,  # Digital/SPI config parameters.
    0x0001: 0x00,  # Digital/SPI config parameters.
    0x000A: 0x00,  # Scratch pad register.
    0x0013: 0x01,  # Set SDO level to 3V3.
    0x0100: 0xFF,  # RX/LO amplifier and bias power-up/down.
    0x0103: 0x15,  # Disable DC detector.
    0x0105: 0x91,  # DC IF amp current control; +- 0%.
    0x0106: 0x0F,  # RX DSA set to 15 dB; 23 - 25 GHz range.
    0x0108: 0xDF,  # DC LO amp I mixer image rejection calibration current.
    0x0109: 0x5F,  # DC LO amp Q mixer image rejection calibration current.
    0x010A: 0x66,  # DC positive mixer gate biasing, I.
    0x010B: 0x66,  # DC negative mixer gate biasing, I.
    0x010C: 0x66,  # DC positive mixer gate biasing, Q.
    0x010D: 0x66,  # DC negative mixer gate biasing, Q; BB amp CM controls.
    0x010E: 0x80,  # DC BB amplifier I output offset calibration.
    0x010F: 0x80,  # DC BB amplifier Q output offset calibration.
    0x0110: 0x09,  # DC BB amplifier controls.
    0x0111: 0x96,  # DC BB amplifier gain controls.
    0x0112: 0x00,  # DC IF amplifier I/Q gain control, fine. Default 0 dB, 0.1 dB steps.
    0x0113: 0x11,  # DC IF amp I/Q gain control, coarse. Default is 1 dB, 1 dB steps.
    0x0116: 0x73,  # LO controls. Same phase shift for UC/DC. Min. LO attens. x2 mode.
    0x0117: 0x00,  # MSB for UC phase shifter. Not used with phase shifters linked.
    0x0118: 0x00,  # LSB for UC phase shifter. Not used with phase shifters linked.
    0x0119: 0x00,  # MSB for DC phase shifter. Controls RX/TX by default.
    0x011A: 0x00,  # LSB for DC phase shifter. Controls RX/TX by default.
    0x011F: 0x04,  # DC detector range; set to -15.5 to 0.5 dBm.
    0x0121: 0xC0,  # Probe calibration settings.
    0x0122: 0x80,  # RX power mode; default is 0% current reduction.
    0x0123: 0xB7,  # LO DSA part 2. Links DC/UC by default. Set DSA with 0x0116.
    0x0200: 0x3D,  # UC bias/amp/chip power-up/down.
    0x0201: 0x01,  # UC bias/amp power-up/down.
    0x0202: 0x96,  # TX power mode part 1.
    0x0203: 0x94,  # TX power mode part 2.
    0x0205: 0x6A,  # UC mixer gate biasing in BB mode.
    0x0207: 0x00,  # UC LO I amp phase adjust (sideband rejection calibration).
    0x0208: 0x00,  # UC LO Q amp phase adjust (sideband rejection calibration).
    0x0209: 0x27,  # UC IF, LO enable/disable.
    0x020A: 0xFF,  # UC DSAs attenuation.
    0x020C: 0xAC,  # UC DSA frequency range.
    0x020D: 0x7A,  # UC TX temperature compensation settings.
    0x020E: 0x00,  # UC LO nulling controls, I.
    0x020F: 0x00,  # UC LO nulling controls, Q.
    0x0210: 0x2C,  # UC LO nulling controls, general.
    0x0216: 0x80,  # UC ADC settings.
    0x0217: 0x80,  # UC ADC enable/controls.
    0x0219: 0x38,  # UC IF amp gain settings; envelope detector settings.
    0x021A: 0x3F,  # UC mixer filter.
}


class Mixer:
    def __init__(self):
        """Initialize rf_cpld class"""
        self.mixer = admv_r_w.SPI_ADMV("admv")
        cha = [0, 1, 2, 3]
        for path in cha:
            self.restore_defaults(0, path)

    def read_mixer_register(
        self, shf_id: int, path: int, address: int, read_tries: int = 5
    ) -> int:
        """Read a value from a RF FPGA register
        TESTED: No
        :param shf_id: board 0; 0=vertical
        :param address: The address of the register to write
        :param read_tries: Number of read tries
        :return:
        """
        data = self.mixer.spi_peek(path, address)
        return data

    def get_tx_attenuation(self, shf_id: int, path: int) -> int:
        """Get the total attenuation of the 2 TX DSAs
        TESTED: No
        :param shf_id: board 0, 1; 0=vertical, 1=horizontal
        :param path: {0|1|2|3}
        :return: DSA attenuation value [dB]
        """
        atten_db = self.get_tx_attenuator1(shf_id, path) + self.get_tx_attenuator2(
            shf_id, path
        )
        return atten_db

    def get_tx_attenuator1(self, shf_id: int, path: int) -> int:
        """Get the attenuation of TX DSA1
        TESTED: No
        :param shf_id: board 0, 1; 0=vertical, 1=horizontal
        :param path: {0|1|2|3}
        :return: DSA1 attenuator value [dB]
        """
        return self.read_mixer_register(shf_id, path, 0x20A) & 0x0F

    def get_tx_attenuator2(self, shf_id: int, path: int):
        """Get the attenuation of TX DSA2
        TESTED: No
        :param shf_id: board 0, 1; 0=vertical, 1=horizontal
        :param path: {0|1|2|3}
        :return: DSA2 attenuator value [dB]
        """
        return (self.read_mixer_register(shf_id, path, 0x20A) & 0xF0) >> 4

    def get_rx_attenuation(self, shf_id: int, path: int) -> int:
        """Get the attenuation of the RX DSA
        TESTED: No
        :param shf_id: board 0, 1; 0=vertical, 1=horizontal
        :param path: {0|1|2|3}
        :return: RX DSA attenuation value [dB]
        """
        # Mask off frequency control bits
        return self.read_mixer_register(shf_id, path, 0x106) & 0xF

    def get_temperature(self, shf_id: int, path: int) -> int:
        """Read the mixer's internal temperature sensor.
        Tested: Yes.
        The conversion formula for raw ADC reading to temperature is based
        on the plot in p. 62 of the mixer datasheet. The plot isn't super
        detailed so this is probably only accurate to within a few degrees C.
        :param shf_id: board 0, 1; 0=vertical, 1=horizontal
        :param path: {0|1|2|3}
        :return: Case temperature [C], read from the mixer's internal temp sensor.
        """
        # Make sure ADC is powered on.
        adc_enable_reg = self.read_mixer_register(shf_id, path, 0x201) & 0xFE
        self.write_mixer_register(shf_id, path, 0x201, adc_enable_reg)

        # Enable the internal ADC clock.
        self.write_mixer_register(shf_id, path, 0x216, 0x88)

        # Enable ADC and set the ADMV ADC mux to the temperature sensor.
        self.write_mixer_register(shf_id, path, 0x217, 0xB0)

        # Start conversions on the ADC.
        self.write_mixer_register(shf_id, path, 0x210, 0xAC)

        # Sleep. Ideally 1ms but python can't handle that, so try 10ms.
        time.sleep(0.01)

        # Get the ADC value.
        adc_raw = self.read_mixer_register(shf_id, path, 0x218)

        # Disable ADC clock and restore original ADC mux settings.
        self.write_mixer_register(shf_id, path, 0x216, 0x80)
        self.write_mixer_register(shf_id, path, 0x217, 0x80)

        # Convert ADC value to temperature in degrees C.
        slope = (190 - 95) / (85 - (-40))
        x, y = -40, 95
        temp = int(x - ((y - adc_raw) / slope))

        return temp

    def set_tx_attenuation(self, shf_id: int, path: int, atten_db: int):
        """Sets the attenuation of mixer TX DSAs
        Note: attenuation passed as float will be rounded down
        TESTED: No
        :param shf_id: board 0, 1; 0=vertical, 1=horizontal
        :param path: {0|1|2|3}
        :param atten_db: TX DSA attenuation [dB]
        """
        # Check attenuation within DSA limits.
        if atten_db < 0 or atten_db > 30:
            raise IOError("Attenuation must be between 0 and 30 dB in 1 dB increments")

        # If we're only setting the LSB in the register, can write directly.
        if atten_db <= 15:
            return self.write_mixer_register(shf_id, path, 0x20A, int(atten_db))

        # If attenuation > 15, need to split up amongst the two DSAs.
        # Distribute first 15 dB to DSA1, then any remaining attenuation to DSA2.
        else:
            atten1 = 15
            atten2 = atten_db - atten1
            atten_db = atten2 << 4 | atten1
            return self.write_mixer_register(shf_id, path, 0x20A, int(atten_db))

    def set_tx_attenuator1(self, shf_id: int, path: int, atten_db: int):
        """Sets the attenuation of mixer DSA1
        Note: attenuation passed as float will be rounded down
        TESTED: No
        :param shf_id: board 0, 1; 0=vertical, 1=horizontal
        :param path: {0|1|2|3}
        :param atten_db: TX DSA1 attenuation [dB]
        """
        atten_db = int(atten_db)
        if atten_db < 0 or atten_db > 15:
            raise IOError("Attenuation must be between 0 and 15 dB in 1 dB increments")

        atten2_db = self.read_mixer_register(shf_id, path, 0x20A) & 0xF0
        reg_val = int(atten_db) | atten2_db
        return self.write_mixer_register(shf_id, path, 0x20A, reg_val)

    def set_tx_attenuator2(self, shf_id: int, path: int, atten_db: int):
        """Sets the attenuation of mixer DSA2
        Note: attenuation passed as float will be rounded down
        TESTED: No
        :param shf_id: board 0, 1; 0=vertical, 1=horizontal
        :param path: {0|1|2|3}
        :param atten_db: TX DSA2 attenuation [dB]
        """
        # Cast to force integer; setting from EEPROM may pass a float.
        atten_db = int(atten_db)
        if atten_db < 0 or atten_db > 15:
            raise IOError("Attenuation must be between 0 and 15 dB in 1 dB increments")

        atten1_db = self.read_mixer_register(shf_id, path, 0x20A) & 0x0F
        reg_val = int(atten_db << 4) | atten1_db
        return self.write_mixer_register(shf_id, path, 0x20A, reg_val)

    def set_rx_attenuation(
        self, shf_id: int, path: int, atten_db: int, rf_freq_ghz: float
    ):
        """Sets the attenuation of the mixer RX DSA
        Note: attenuation passed as float will be rounded down
        Also sets the frequency control bits. Mapping from ADMV CPLD spec
        TESTED: No
        :param shf_id: board 0, 1; 0=vertical, 1=horizontal
        :param path: {0|1|2|3}
        :param atten_db: TX DSA1 attenuation [dB]
        :param rf_freq_ghz: RF frequency [GHz]
        """
        atten_db = int(atten_db)
        if atten_db < 0 or atten_db > 15:
            raise IOError("Attenuation must be between 0 and 15 dB in 1 dB increments")

        if rf_freq_ghz > 25.0:
            reg_val = int(atten_db) | 0x10
        else:
            reg_val = atten_db

        return self.write_mixer_register(shf_id, path, 0x106, reg_val)

    def write_mixer_register(
        self, shf_id: int, path: int, address: int, value: int, max_tries: int = 5
    ):
        """Write a value to a shf register
        TESTED: No
        :param shf_id: board 0, 1; 0=vertical, 1=horizontal
        :param path: {0|1|2|3}
        :param address: The address of the register to write
        :param value: The value to write
        :param max_tries: The number of tries to write a register
        :return:
        """
        self.mixer.spi_poke(path, address, value)

    def enable_mixer(self, shf_id: int, path: int) -> None:
        """Enable the converters on the selected ADMV.
        NOTE: This method enables the upconverter and downconverter. The TR line
        toggling will activate/deactivate each section of the IC as appropriate.
        TESTED: NO.
        :param shf_id: board 0, 1; 0=vertical, 1=horizontal
        :param path: {0|1|2|3}
        """
        # Map of registers and values to write to enable the mixer.
        mixer_configs = {
            0x100: 0x20,  # Powers up the LO chain bias, LO band-gap, downconverter.
            0x200: 0x38,  # Powers upconverter and upconverter band-gap.
            0x201: 0x7E,  # Enable IF/RF amp bias; ADC.
            0x209: 0x2F,  # Enable upconverter IF mode.
        }

        # Enable upconversion.
        for address, value in mixer_configs.items():
            self.write_mixer_register(shf_id, path, address, value)

    def disable_mixer(self, shf_id: int, path: int) -> None:
        """Disable the converters on the selected ADMV.
        NOTE: This method disables the upconverter and downconverter. The TR line
        toggling will do nothing.
        TESTED: NO.
        :param shf_id: board 0, 1; 0=vertical, 1=horizontal
        :param path: {0|1|2|3}
        """
        # Map of registers and values to write to disable the mixer.
        mixer_configs = {
            0x100: 0xFF,  # Disable the LO chain and downconverter.
            0x200: 0x3D,  # Power down upconverter and upconverter band-gap.
            0x201: 0x01,  # Disable IF/RF amp bias; ADC.
            0x209: 0x27,  # Disable upconverter IF mode.
        }

        # Disable mixer.
        for address, value in mixer_configs.items():
            self.write_mixer_register(shf_id, path, address, value)

    def enable_upconverter(self, shf_id: int, path: int) -> None:
        """Put the selected ADMV into upconverter mode.
        NOTE: This will enable the upconverter only. Use "enable/disable_mixer"
        to configure the mixer like it will be in the field.
        :param shf_id: board 0, 1; 0=vertical, 1=horizontal
        :param path: {0|1|2|3}
        """
        # Map of registers and values to write to enable upconversion.
        upconverter_configs = {
            0x100: 0xF3,  # Powers up the LO chain bias and LO band-gap.
            0x200: 0x38,  # Powers upconverter and upconverter band-gap.
            0x201: 0x7E,  # Enable IF/RF amp bias; ADC.
            0x209: 0x2F,  # Enable upconverter IF mode.
        }

        # Enable upconversion.
        for address, value in upconverter_configs.items():
            self.write_mixer_register(shf_id, path, address, value)

    def disable_upconverter(self, shf_id: int, path: int) -> None:
        """Disable the upconverter on the selected ADMV.
        NOTE: This will disable the upconverter only. Use "enable/disable_mixer"
        to configure the mixer like it will be in the field.
        :param shf_id: board 0, 1; 0=vertical, 1=horizontal
        :param path: {0|1|2|3}
        """
        # Map of registers and values to write to disable upconversion.
        upconverter_configs = {
            0x100: 0xFF,  # Disable the LO chain.
            0x200: 0x3D,  # Power down upconverter and upconverter band-gap.
            0x201: 0x01,  # Disable IF/RF amp bias; ADC.
            0x209: 0x27,  # Disable upconverter IF mode.
        }

        # Disable upconversion.
        for address, value in upconverter_configs.items():
            self.write_mixer_register(shf_id, path, address, value)

    def enable_downconverter(self, shf_id: int, path: int) -> None:
        """Enable the downconverter chain on the selected ADMV.
        NOTE: This will enable the downconverter only. Use "enable/disable_mixer"
        to configure the mixer like it will be in the field.
        :param shf_id: board 0, 1; 0=vertical, 1=horizontal
        :param path: {0|1|2|3}
        """
        # Map of registers and values to write to enable downconverter.
        downconverter_configs = {
            0x100: 0x20  # Enable LO chain and downconverter bias/amps.
        }

        # Enable downconversion.
        for address, value in downconverter_configs.items():
            self.write_mixer_register(shf_id, path, address, value)

    def disable_downconverter(self, shf_id: int, path: int) -> None:
        """Disable the downconverter chain on the selected ADMV.
        NOTE: This will disable the downconverter only. Use "enable/disable_mixer"
        to configure the mixer like it will be in the field.
        :param shf_id: board 0, 1; 0=vertical, 1=horizontal
        :param path: {0|1|2|3}
        """
        # Map of registers and values to write to disable downconverter.
        downconverter_configs = {
            0x100: 0xF3  # Disable downconverter amps/bias; leave LO chain enabled.
        }

        # Disable downconversion.
        for address, value in downconverter_configs.items():
            self.write_mixer_register(shf_id, path, address, value)

    def set_phase_shifter(self, shf_id: int, path: int, phase: int):
        """
        set the phase shifter to a specific decimal value
        The decimal values can range from 0 to 2048 and do not correspond directly
        to a phase shift in degrees. There is also overlap between decimal values
        and the amount of phase shift in degrees. Meaning multiple decimal values
        will results in the same amount of phase shift in degrees.
        Refer to Analog Devices ADMV1018 data sheet (ADMV1018_RevSp0_Final_DS_DEC_12_2019_Starry_10Jan2020 (2).pdf)
        in the LO PHASE CONTROL section on page 54 for more information.
        :param shf_id: board 0, 1; 0=vertical, 1=horizontal
        :param path: {0|1|2|3}
        :param value: an int from 0 to 2048
        """
        lsb, msb = self.calc_phase_msb_lsb(phase)

        self.write_mixer_register(shf_id=shf_id, path=path, address=0x119, value=lsb)
        self.write_mixer_register(shf_id=shf_id, path=path, address=0x11A, value=msb)

    @staticmethod
    def calc_phase_msb_lsb(phase_decimal: int):
        hex_str = hex(phase_decimal)
        hex_str = hex_str[2:]  # get rid of 0x

        if len(hex_str) == 3:
            msb = int(hex_str[0], 16)
            lsb = int(hex_str[1:], 16)
        if len(hex_str) <= 2:
            msb = 0
            lsb = int(hex_str, 16)

        return (lsb, msb)

    def restore_defaults(self, shf_id: int, path: int) -> None:
        """Restore Starry default register values on the selected ADMV.
        TESTED: Yes.
        :param shf_id: board 0, 1; 0=vertical, 1=horizontal
        :param path: {0|1|2|3}
        """
        for address, value in STARRY_DEFAULTS.items():
            self.write_mixer_register(shf_id, path, address, value)
