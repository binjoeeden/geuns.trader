import sys
from setting_io import *

setting = None

def getSettings():
    global setting
    settings = Settings()
    settings.loadSettings()
    setting = settings.getSettings()
    return setting

def getCoinConfig():
    global setting
    getSettings()
    # print("setting : "+str(setting))
    crcys = setting['system']['crcy']
    setting['crcy_list'] = []
    config = {}
    crcy_list = []
    for crcy in crcys.split(','):
        crcy = crcy.strip()
        if crcy=='':
            continue
        crcy = crcy.strip()
        crcy_list.append(crcy)
        try:
            config[crcy] = setting[crcy]
        except:
            config[crcy] = setting['common']

    for e in setting['common'].keys():
        for crcy in crcy_list:
            if e in config[crcy].keys():
                continue
            else:
                config[crcy][e] = setting['common'][e]

    config['crcy_list'] = crcy_list
    return config
