import os


def get_set_i2c_back():
    bashCommand = "gpio -g mode 2 alt0"
    os.system(bashCommand)
    bashCommand = "gpio -g mode 3 alt0"
    os.system(bashCommand)
    return None
