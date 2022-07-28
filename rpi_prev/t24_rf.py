import t24_fpga


class SHF:
    """SHF wrapper class (RF board only)"""
    def __init__(self):
        """Initialize rf_cpld class
        """
        self.fpga = t24_fpga.spi("rf")
        

    def read_rf_register(self, shf_id: int=0, address: int, read_tries: int = 5) -> int:
        """Read a value from a RF FPGA register
        TESTED: No
        :param shf_id: board 0; 0=vertical 
        :param address: The address of the register to write
        :param read_tries: Number of read tries
        :return:
        """
        data = self.fpga.peek(address)
        return data
    def write_rf_register(      
            self, shf_id: int=0, address: int, value: int, max_tries: int = 5
        ):
            """Write a value to the FPGA shf register
            TESTED: No
            :param shf_id: board 0
            :param address: The address of the register to write
            :param value: The value to write
            :param max_tries: The number of tries to write a register
            :return:
            """

            value = int(value)
            self.fpga.poke(address, value)
    def set_lo_attenuator(self, shf_id: int, atten_db: int) -> int:
        """Sets the LO attenuation.
        Note: attenuation passed as float will be rounded down
        TESTED: No
        :param shf_id: board 0, 1; 0=vertical, 1=horizontal
        :param atten_db: LO attenuation value in dB
        """
        if atten_db < 0 or atten_db > 31:
            raise IOError("Attenuation must be between 0 and 31 dB in 1 dB increments")

        return self.write_rf_register(shf_id, 0xC, int(atten_db))
    
        
    def set_rf_rx_attenuator(
        self, shf_id: int, path: int, atten_db: float, path_on: bool = True
    ):
        """Set RF RX attenuator
        TESTED: No
        :param shf_id: board 0, 1; 0=vertical, 1=horizontal
        :param path: {0|1|2|3}
        :param atten_db: attenuation value in dB
        :param path_on: is path enabled boolean
        """

        if atten_db < 0 or atten_db > 31.5:
            raise IOError(
                "Attenuation must be between 0 and 31.5 dB in 0.5 dB increments"
            )

        reg_val = int(round(atten_db * 2))

        if not path_on:
            reg_val = reg_val | 0b01000000

        self.write_rf_register(shf_id, path + 4, reg_val)

    def set_mode(self, tr_mode: str, rf_boards: list = [0, 1]):
        """Sets the mode of the RF/IF board
        :param tr_mode: TR mode to set {disable|normal|rx|tx}
        :param rf_boards: List of RF boards to configure
        TESTED: No
        """
        tr_modes = {"disable": 0, "normal": 1, "rx": 2, "tx": 3}


        if tr_mode in tr_modes.keys():
            reg_val = tr_modes[tr_mode]
        else:
            raise IOError("Not a mode, choose from: disable, normal, rx, tx")

        # Set RF tr mode
        for shf_id in rf_boards:
            self.write_rf_register(shf_id, 0x3, reg_val)



    def set_rf_tx_attenuator(
        self,
        shf_id: int,
        path: int,
        atten_db: float,
        path_on: bool = False,
    ):
        """Set RF TX attenuator
        TESTED: No
        :param shf_id: board 0, 1; 0=vertical, 1=horizontal
        :param path: {0|1|2|3}
        :param atten_db: attenuation value in dB
        :param path_on: if path is enabled boolean. if True, enables amps
        """

        if atten_db < 0 or atten_db > 31.5:
            raise IOError(
                f"Attenuation must be between 0 and 31.5 dB in 0.25-0.5 dB increments"
            )
        

        reg_val = int(round(atten_db * 4))

        if path_on:
            reg_val = reg_val | 0b110000000

        self.write_rf_register(shf_id, path + 8, reg_val)
    
