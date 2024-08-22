from pathlib import Path
import json


class Config:
    def __init__(self, config_path=None):
        if config_path is None:
            base_path = Path(__file__).parent
            config_path = base_path / '../settings/settingPRIVATE.json'

        config_path = config_path.resolve()

        with config_path.open('r') as config_file:
            config = json.load(config_file)
            self.API_ID = config['API_ID']
            self.API_HASH = config['API_HASH']
            self.PHONE = config['PHONE']
            self.USERS = config["USERS"]
            self.MONGO_URL = config["MONGO_URL"]
            self.DISCORD_TOKEN_URL = config["DISCORD_TOKEN_URL"]
            self.DISCORD_AUTH_URL = config["DISCORD_AUTH_URL"]


config = Config()

