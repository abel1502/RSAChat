import utils


class Config:
    parser = None
    path = None
    
    def Initialize(path="config/config.ini"):
        utils.checkParamTypes("config.Config.Initialize", [path], [{str}])
        Config.parser = utils.openIni(path)
        Config.path = path
    
    def getValue(section, key, default=None):
        utils.checkParamTypes("config.Config.getValue", [section, key], [{str}, {str}])
        try:
            return Config.parser[section][key]
        except:
            return default
    

Config.Initialize()
