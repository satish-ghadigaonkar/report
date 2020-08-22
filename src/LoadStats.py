import configparser
from configparser import NoSectionError

class ConfigParser(configparser.ConfigParser):
    """Can get options() without defaults
    """
    def options(self, section, no_defaults=False, **kwargs):
        if no_defaults:
            try:
                return list(self._sections[section].keys())
            except KeyError:
                raise NoSectionError(section)
        else:
            return super().options(section, **kwargs)

class LoadStats:
    def __init__(self, stats=None, labelconfig=None, labelsection="DEFAULT", formatconfig=None, formatsection="DEFAULT",
                 templateconfig=None, templatesection="DEFAULT"):
        self.stats = stats
        self.labelconfig = labelconfig
        self.labelsection = labelsection
        self.formatconfig = formatconfig
        self.formatsection = formatsection
        self.templateconfig = templateconfig
        self.templatesection = templatesection

    def _readconfig(self, configfile):
        config = ConfigParser()

        config.optionxform = lambda option: option
        config.read(configfile)
        return config

    def _formatlabel(self, stat):
        config = self._readconfig(self.labelconfig)

        return config[self.labelsection if self.labelsection in config else config.default_section].get(stat, stat)

    def _formatvalue(self, stat, value):
        config = self._readconfig(self.formatconfig)

        if value is not None:
            return config[self.formatsection if self.formatsection in config else config.default_section].get(stat,
                                                                                                              '{}').format(
                value)
        else:
            return '-'

    def _applytemplatetolabel(self, key):
        config = self._readconfig(self.templateconfig)
        return config[self.templatesection if self.templatesection in config else config.default_section][key].format(
            *(self._formatlabel(string.strip()) for string in key.split(',')))

    def _applytemplatetovalue(self, key):
        config = self._readconfig(self.templateconfig)
        return config[self.templatesection if self.templatesection in config else config.default_section][key].format(
            *(self._formatvalue(string.strip(), self.stats.get(string.strip(), None)) for string in key.split(',')))

    def getstats(self):
        config = self._readconfig(self.templateconfig)

        if config.has_section(self.templatesection):
            return ((self._applytemplatetolabel(key), self._applytemplatetovalue(key), i) for i, key in
                    enumerate(config.options(self.templatesection, no_defaults=True)))
        else:
            return ((self._applytemplatetolabel(key), self._applytemplatetovalue(key), i) for i, key in
                    enumerate(config[config.default_section].keys()))


# stats = LoadStats(configfile=r"C:\Users\sasg\PycharmProjects\report\src\output\config.txt", stats={
#     "count": 1,
#     "mean": 1.63,
#     "std": 0.0946484724300046,
#     "median": 1.63,
#     "min": 1.63,
#     "max": 1.63
# })
#
# print(list(stats.getstats()))
