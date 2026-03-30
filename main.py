import os
import configparser
from utils.farm_bot_cv import FarmBotCV

config_path = "config.ini"
config = configparser.ConfigParser(inline_comment_prefixes=('#',))
config.read(config_path,encoding="utf-8")

check_interval = config.getfloat('bot', 'check_interval')
debug_mode = config.getboolean('bot', 'debug_mode')        

bot = FarmBotCV(check_interval, debug_mode, config)
bot.start()






