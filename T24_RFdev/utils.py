"""Utils for titan24_prototypes"""
import sys
import logging
from pathlib import Path
from logging import Logger
from subprocess import check_output, CalledProcessError

try:
    import yaml
except ModuleNotFoundError:
    print("Couldn't import yaml")

DEFAULT_ARMADA_IP = "192.168.100.1"
DEFAULT_QSR_IP = "192.168.100.25"

CHANNEL_MAP = {36: 5.25, 100: 5.57}
ANT_MAP = ["V0", "H3", "V1", "H2", "H0", "V3", "H1", "V2"]
# TODO: Double check that it's not the other one:
# ANTMAP = ["V0", "H3", "V1", "H2", "V2", "H1", "V3", "H0"]

SUCCESS_LEVEL = 25


def load_yaml(filename):
    with open(filename, "r") as ifile:
        return yaml.load(ifile, Loader=yaml.UnsafeLoader)


def save_yaml(filename, data):
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    with open(filename, "w+") as outfile:
        yaml.dump(data, outfile, default_flow_style=False, sort_keys=False)


def save_file(filename, data_str):
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    with open(filename, "w+") as outfile:
        outfile.write(data_str)


class ColorFormatter(logging.Formatter):
    """Sets Up Colored Formatting"""

    warning_fmt = "\033[95m%(levelname)s: %(msg)s\033[0m"
    error_fmt = "\033[91m%(levelname)s: %(msg)s\033[0m"
    success_fmt = "\033[32m%(levelname)s: %(msg)s\033[0m"
    info_fmt = "%(msg)s"
    debug_fmt = "%(levelname)s: %(msg)s"

    def __init__(self, fmt="%(levelname)s: %(msg)s"):
        logging.Formatter.__init__(self, fmt)

    def format(self, record):
        format_orig = self._style._fmt
        if record.levelno <= logging.DEBUG:
            self._style._fmt = self.debug_fmt
        elif record.levelno == logging.INFO:
            self._style._fmt = self.info_fmt
        elif record.levelno == SUCCESS_LEVEL:
            self._style._fmt = self.success_fmt
        elif record.levelno == logging.ERROR:
            self._style._fmt = self.error_fmt
        else:
            self._style._fmt = self.warning_fmt
        result = logging.Formatter.format(self, record)
        self._style._fmt = format_orig
        return result


def add_logging_level(level_name: str, level_num: int, method_name: str = None) -> None:
    """
    Grabbed from: https://github.com/visinf/deblur-devil/commit/
    0a6772ac2f589aa1dca182b880b6c8ee36def72c
    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.
    e.g. addLoggingLevel('TRACE', logging.DEBUG - 5)

    :param level_name:
    :param level_num:
    :param method_name:
    :return:
    """
    if not method_name:
        method_name = level_name.lower()
    if hasattr(logging, level_name):
        raise AttributeError("{} already defined in logging module".format(level_name))
    if hasattr(logging, method_name):
        raise AttributeError("{} already defined in logging module".format(method_name))
    if hasattr(logging.getLoggerClass(), method_name):
        raise AttributeError("{} already defined in logger class".format(method_name))

    # This method was inspired by the answers to Stack Overflow post
    # http://stackoverflow.com/q/2183233/2988730, especially
    # http://stackoverflow.com/a/13638084/2988730
    def log_for_level(self, message, *args, **kwargs):
        if self.isEnabledFor(level_num):
            self._log(level_num, message, args, **kwargs)

    def log_to_root(message, *args, **kwargs):
        logging.log(level_num, message, *args, **kwargs)

    logging.addLevelName(level_num, level_name)
    setattr(logging, level_name, level_num)
    setattr(logging.getLoggerClass(), method_name, log_for_level)
    setattr(logging, method_name, log_to_root)


def wait_for_qtn() -> None:
    # dont need the whole traceback, set level to 0 temporarily
    sys.tracebacklimit = 0
    try:
        check_output("systemctl status qtn-config", shell=True)
    except CalledProcessError:
        print("Qtn not up yet! Try again later.")
        raise ConnectionError() from None
    sys.tracebacklimit = 1000  # default is 1000


def set_up_logging(debug=False) -> Logger:
    """Set up the handlers for logging titan24_prototypes to stderr."""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    stderr_handler = logging.StreamHandler()
    stderr_formatter = ColorFormatter()
    stderr_handler.setFormatter(stderr_formatter)
    if debug:
        stderr_handler.setLevel(logging.DEBUG)
    else:
        stderr_handler.setLevel(logging.INFO)
    logger.addHandler(stderr_handler)

    add_logging_level("SUCCESS", SUCCESS_LEVEL, method_name=None)
    return logger
