import log as Log
from config import AppConfig


# load environment variables
appconfig = AppConfig()
# load env vars
appconfig.load_from_envar()

Log.init(appconfig)