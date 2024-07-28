import json


class Config:
    def __init__(self, config_path='../settings/settingPRIVATE.json'):
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
            self.API_ID = config['API_ID']
            self.API_HASH = config['API_HASH']
            self.PHONE = config['PHONE']
            self.USERS = config["USERS"]
            self.MONGO_URL = config["MONGO_URL"]
            self.DISCORD_TOKEN_URL = config["DISCORD_TOKEN_URL"]
            self.DISCORD_AUTH_URL = config["DISCORD_AUTH_URL"]


config = Config()
