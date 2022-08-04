"""SPI Bus control for Raspberry Pi 3b"""

import RPi.GPIO as GPIO


class Spi:

    """Abstracted SPI bus class for Raspberry PIs"""

    def __init__(self, cpld_type):
        """Define pins based on cpld_type"""
        if cpld_type.lower() == "rf":
            self.ss_pin = 24
            self.sclk_pin = 23
            self.mosi_pin = 19
            self.miso_pin = 21
            self.type = "rf"
        else:
            raise IOError('incorrect cpld_type.  Only  "rf" available')
        self.config()

    def config(self):
        """Configure GPIO on RP3"""

        # set GPIO numbering to board pinout mode
        GPIO.setmode(GPIO.BOARD)
        # supress warnings if GPIO are out of board defaults
        GPIO.setwarnings(False)

        # Define output Pins
        GPIO.setup((self.ss_pin, self.sclk_pin, self.mosi_pin), GPIO.OUT)
        # Define Input Pins
        GPIO.setup((self.miso_pin), GPIO.IN)
        # Set output pin High/Low States
        GPIO.output(
            (self.ss_pin, self.sclk_pin, self.mosi_pin), (GPIO.HIGH, GPIO.LOW, GPIO.LOW)
        )

    def send_byte(self, value):
        """Send byte <value> by toggling Spi Clock"""

        # valuse is assumed to be a decimal string
        # need to convert to binary list
        data = list("{0:08b}".format(value))
        for bits in data:
            GPIO.output(self.mosi_pin, int(bits))  # express data bit
            GPIO.output(self.sclk_pin, GPIO.HIGH)  # clock high
            GPIO.output(self.sclk_pin, GPIO.LOW)  # clock low

    def read16(self):
        """Read <read_data> by toggling Spi Clock"""
        GPIO.output(self.sclk_pin, GPIO.LOW)
        data = []

        for _ in range(16):
            data.append(GPIO.input(self.miso_pin))
            GPIO.output(self.sclk_pin, GPIO.HIGH)
            GPIO.output(self.sclk_pin, GPIO.LOW)

        read_data = int("".join(map(str, data)), 2)
        # print("read_data={}".format(read_data))

        return read_data

    def peek(self, address):
        """Read Register at <address>"""
        # send address (8 bits)
        # capture 16-bit read value

        # For register reads, need to set final bit to 1
        self.config()
        address <<= 0x1
        address |= 0x1
        GPIO.output(self.ss_pin, 0)
        GPIO.output(self.sclk_pin, 0)

        self.send_byte(address)
        data = self.read16()

        GPIO.output(self.ss_pin, 1)
        address = address >> 1

        # print("CPLD READ A:0x{:02x} D:0x{:04x}".format(address, data))
        data = "{:04x}".format(data)
        return data

    def poke(self, address, write_value):
        """Write <write_value> at register <address>"""

        # shift left 1 (leaving zero at bit 0) for write
        self.config()
        address <<= 0x1

        upper = write_value >> 8
        lower = write_value & 255
        GPIO.output(self.ss_pin, 0)
        GPIO.output(self.sclk_pin, 0)

        for i in (address, upper, lower):
            self.send_byte(i)

        GPIO.output(self.ss_pin, 1)
        address = address >> 1

        # print("CPLD WRITE A:0x{:02x} D:0x{:04x}".format(address, write_value))

    @staticmethod
    def clean_up():
        """Cleanup GPIO on RP3 to defaults"""
        GPIO.cleanup()
