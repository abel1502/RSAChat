from . import utils

if "Config" not in globals():
    Config = utils.IniParser("config/config.ini")
    get = Config.get
    set = Config.set