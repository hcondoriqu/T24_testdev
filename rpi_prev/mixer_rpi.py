import admv_r_w


class Mixer:
    def __init__(self):
        """Initialize rf_cpld class"""
        self.mixer = admv_r_w.SPI_ADMV("admv")

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
