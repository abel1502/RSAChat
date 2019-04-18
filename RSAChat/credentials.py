from . import utils

if "Credentials" not in globals():
    Credentials = utils.IniParser("config/credentials.ini")
    get = Credentials.get
    set = Credentials.set 
