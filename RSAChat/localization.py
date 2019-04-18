from . import utils
from . import config

if "Localization" not in globals():
    Localization = utils.IniParser("config/localization.ini")
    get = Localization.get
    set = Localization.set