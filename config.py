import configparser
import os
import utils


class Config:
    parser = None
    path = None
    
    def Initialize(path="config/config.ini"):
        utils.checkParamTypes("config.Config.Initialize", [path], [{str}])
        if Config.path is None:
            Config.parser = configparser.ConfigParser()
            if not (os.path.exists(path) and os.path.isfile(path)):
                utils.showWarning("config.Config.Initialize", "Config file missing")
                if not os.path.exists(os.path.dirname(path)):
                    os.mkdir(os.path.dirname(path))
                if os.path.exists(path) and not os.path.isfile(path):
                    utils.raiseException("config.Config.Initialize", "Specified config path points to a directory")
                if not os.path.exists(path):
                    open(path, "w").close()
            Config.parser.read(path)
            Config.path = path
    
    def getValue(section, key, default=None):
        utils.checkParamTypes("config.Config.getValue", [section, key], [{str}, {str}])
        try:
            return Config.parser[section][key]
        except:
            return default
    

Config.Initialize()
