import configparser
import math

class LoadLabels:
    def __init__(self, labelconfig = None, labelsection="DEFAULT", labelorderconfig = None, labelordersection="DEFAULT"):
        self.labelconfig = labelconfig
        self.labelsection = labelsection
        self.labelorderconfig = labelorderconfig
        self.labelordersection= labelordersection

    def _readconfig(self, configfile):
        config = configparser.ConfigParser(delimiters=('~', '@'))
        config.optionxform = lambda option: option
        config.read(configfile, encoding='UTF-8')
        return config

    def get_formatted_label(self, label):
        config = self._readconfig(self.labelconfig)

        return config[self.labelsection if self.labelsection in config else config.default_section].get(label, label)

    def get_label_order(self, label):
        config = self._readconfig(self.labelorderconfig)
        return config[self.labelordersection if self.labelordersection in config else config.default_section].getfloat(label, math.inf)