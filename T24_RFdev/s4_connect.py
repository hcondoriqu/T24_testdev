"""This module manages the connection to the QSR"""
import time
import socket
import logging
from typing import Optional, Union
from telnetlib import Telnet
from subprocess import check_output
from dataclasses import dataclass, asdict

from utils import DEFAULT_QSR_IP


@dataclass  # pylint: disable=too-many-instance-attributes  # dataclass
class S4ConnectClientConfig:
    """Configuration for S4Connect"""

    hostname: str = DEFAULT_QSR_IP
    telnet_port: int = 23
    newline: str = "\r\n"
    username: str = "root"
    password: Optional[str] = None
    login_prompt: str = "soc1 login: "
    bash_prompt: str = "quantenna # "
    trig: str = "==ENDOFRESPONSE==EXITCODE:"


@dataclass
class S4ConnectServerConfig:
    """Configuration for S4Connect"""

    hostname: Optional[str] = None
    tftp_root = "/var/lib/tftpboot"
    tftp_linkname = "qsr_upload_file"
    logger = logging.getLogger(__name__)

    def __post_init__(self):
        if not self.hostname:
            try:
                self.hostname = socket.gethostbyname(socket.gethostname())
                self.logger.debug(f"Using Autodetected Server IP: {self.hostname}")
            except socket.gaierror:
                self.logger.debug("Could not Autodetect Server IP")


class S4Connect:
    """This class sets up a persistent Telnet connection to the QSR"""

    def __init__(self, client_config, server_config=None, autostart=False):
        self.logger = logging.getLogger(__name__)
        self.client_config = S4ConnectClientConfig(**client_config)
        self.server_config = S4ConnectServerConfig(**server_config)
        if autostart:
            self.conn = self.establish_connection()
        else:
            self.conn = None

    def establish_connection(self):
        """Establish Telnet connection to QSR"""
        conn = Telnet(
            self.client_config.hostname, self.client_config.telnet_port, timeout=2
        )
        conn.read_until(self.client_config.login_prompt.encode())
        conn.write(
            f"{self.client_config.username}{self.client_config.newline}".encode()
        )
        conn.read_until(self.client_config.bash_prompt.encode())
        return conn

    def check_for_conn(self):
        """Establish Telnet connection to QSR if not already established"""
        if self.conn is None:
            self.conn = self.establish_connection()

    def call_qcsapi(self, command: str):
        """Run call_qcsapi command

        :param command: qcsapi command to run
        """
        self.check_for_conn()
        return self.communicate_trig(f"call_qcsapi {command}")[0]

    def starry_moac(self, command: str):
        """Run starry_moac command

        :param command: starry_moac command to run
        """
        return self.call_qcsapi(f"run_script remote_command starry_moac {command}")

    def get_calstate(self, max_retries: int = 5):
        """Get calstate from uboot

        :param max_retries: maximum number of times to try to get valid output
        """
        for _ in range(max_retries):
            calstate = self.call_qcsapi("get_bootcfg_param calstate")
            try:
                calstate = int(calstate)
            except ValueError:
                self.logger.warning(f"Bad calstate {calstate}; Retrying...")
                continue
            break
        return calstate

    def set_calstate(self, calstate: Union[int, str]):
        """Set calstate in uboot if different from current calstate

        :param calstate: {1/'1'} = mfg mode, {2/'2'} = prod mode
        """
        self.check_for_conn()
        current = self.get_calstate()
        if current == calstate:
            self.logger.warning(
                f"Calstate already set to {current}, not doing anything."
            )
            return ""
        if str(calstate) not in ["1", "3"]:
            raise ValueError(f"Invalid Calstate {calstate}; Not Setting")
        self.logger.warning(f"Setting Calstate to {calstate}. Reboot QSR Manually!")
        return self.call_qcsapi(f"update_bootcfg_param calstate {calstate}")

    def write(self, inpt):
        """Write to Telnet stdin"""
        self.check_for_conn()
        # self.logger.debug(f"[TO QSR] {repr(inpt)}")
        self.conn.write(inpt.encode())

    @staticmethod
    def line_is_stdin(line):
        """Check if the incoming line is part of stdin"""
        is_stdin = False
        if line.startswith("> "):
            is_stdin = True
        if line.startswith("quantenna # "):
            is_stdin = True
        return is_stdin

    def readline(self):
        """Read one line from Telnet output buffer"""
        self.check_for_conn()
        outpt = self.conn.read_until(self.client_config.newline.encode()).decode()
        while self.line_is_stdin(outpt):
            outpt = self.conn.read_until(self.client_config.newline.encode()).decode()
        # self.logger.debug(f"[FROM QSR] {repr(outpt)}")
        return outpt

    def readall(self):
        """Read entire Telnet output buffer"""
        self.check_for_conn()
        output = self.conn.read_very_eager().decode()
        # logging.debug(f"[FROM QSR] {repr(output)}")
        return output

    def exit(self):
        """Close Telnet Session"""
        if self.conn is not None:
            self.conn.close()

    def communicate(self, cmd, trig=None, wait=0, throttle=0.1):
        """Send command and return response"""
        self.readall()
        self.write(cmd.strip() + self.client_config.newline)
        if trig:
            self.check_for_conn()
            self.conn.read_until(f"{trig}$?{self.client_config.newline}".encode())
            outpt = ""
            done = False
            while not done:
                line = self.readline()
                if line:
                    outpt += line
                    if trig.strip() in line:
                        done = True
                else:
                    time.sleep(throttle)
            return outpt
        time.sleep(wait)
        return self.readall()

    def communicate_trig(self, cmd, max_retries: int = 5):
        """Send command using a trigger and return response and status"""
        for _ in range(max_retries):
            outpt = self.communicate(
                f"{cmd.strip()};\\{self.client_config.newline}echo {self.client_config.trig}$?",
                trig=self.client_config.trig,
            )
            outpt, status = outpt.split(self.client_config.trig)
            try:
                status = int(status)
            except ValueError:
                self.logger.debug(
                    f"S4 failed to parse QSR command: {cmd} (bad status: '{status}')"
                )
                continue
            if not outpt:
                self.logger.debug(
                    f"S4 failed to parse QSR command: {cmd} (bad output: '{outpt}')"
                )
                continue
            break
        if status:
            self.logger.error(f"QSR Command FAILED with exit code {status}: {cmd}")
        return outpt.strip(), status

    def download_file(self, filename_server, filename_qsr):
        """Download a file or directory from the QSR via TFTP"""
        check_output("systemctl restart tftp".split())
        check_output(
            f"rm -f {self.server_config.tftp_root}/{self.server_config.tftp_linkname}".split()
        )
        self.communicate_trig(
            f"tftp -p -r {self.server_config.tftp_linkname} -l {filename_qsr} "
            f"{self.server_config.hostname}"
        )
        check_output(
            f"cp {self.server_config.tftp_root}/{self.server_config.tftp_linkname} "
            f"{filename_server}".split()
        )
        check_output(
            f"rm -f {self.server_config.tftp_root}/{self.server_config.tftp_linkname}".split()
        )

    def upload_file(self, filename_server, filename_qsr):
        """Upload a file or directory to the QSR via TFTP"""
        check_output("systemctl restart tftp".split())
        check_output(
            f"rm -f {self.server_config.tftp_root}/{self.server_config.tftp_linkname}".split()
        )
        check_output(
            f"cp {filename_server} "
            f"{self.server_config.tftp_root}/{self.server_config.tftp_linkname}".split()
        )
        self.communicate_trig(
            f"tftp -g -r {self.server_config.tftp_linkname} -l {filename_qsr} "
            f"{self.server_config.hostname}"
        )
        check_output(
            f"rm -f {self.server_config.tftp_root}/{self.server_config.tftp_linkname}".split()
        )
