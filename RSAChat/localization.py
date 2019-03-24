from . import utils
from . import config


class Strings:
    parser = None
    path = None
    
    def Initialize(path="config/localization.ini"):
        utils.checkParamTypes("localization.Strings.Initialize", [path], [{str}])
        Strings.parser = utils.openIni(path)
        Strings.path = path
    
    def getValue(key, default=None):
        utils.checkParamTypes("localization.Strings.getValue", [key], [{str}, {str}])
        try:
            return Strings.parser[Config.parser["General"]["Language"]][key]
        except:
            return default
    

Strings.Initialize()