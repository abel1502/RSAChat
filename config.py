import configparser
import os


class Config:
    parser = None
    def Initialize(path="config/config.ini"):
        Config.parser = configparser.ConfigParser()
        if not (os.path.exists(path) and os.path.isfile(path)):
            raise Exception("")  # TODO: Exception text and finish


Config.Initialize()