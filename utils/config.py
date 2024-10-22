import os
from pathlib import Path
from dotenv import load_dotenv


class ConfigError(Exception):
    """Custom exception for configuration errors"""
    pass


class Config:
    def __init__(self, env_path=None):
        if env_path is None:
            base_path = Path(__file__).parent
            env_path = base_path / '../.env'

        env_path = env_path.resolve()

        # Load the environment variables from the .env file
        load_dotenv(dotenv_path=env_path)

        # Fetch the environment variables with checks
        self.API_ID = os.getenv('API_ID')
        self.API_HASH = os.getenv('API_HASH')
        self.PHONE = os.getenv('PHONE')
        self.MONGO_URL = os.getenv('MONGO_URL')
        self.DISCORD_TOKEN_URL = os.getenv('DISCORD_TOKEN_URL')
        self.DISCORD_AUTH_URL = os.getenv('DISCORD_AUTH_URL')
        self.SECRET_KEY = os.getenv('SECRET_KEY')
        self.NAME_CLUSTER = os.getenv('NAME_CLUSTER', "Teledrive")

        # Fetch the port, using 5000 as the default if not set
        self.PORT = os.getenv('PORT', '5000')

        # Validate required configurations
        self.validate()

    def validate(self):
        """Validate all required configurations are loaded properly."""
        missing = []

        # Check each required config, add to missing list if not found
        if not self.API_ID:
            missing.append('API_ID')
        if not self.API_HASH:
            missing.append('API_HASH')
        if not self.PHONE:
            missing.append('PHONE')
        if not self.MONGO_URL:
            missing.append('MONGO_URL')
        if not self.SECRET_KEY:
            missing.append('SECRET_KEY')

        # If any required configuration is missing, raise an error
        if missing:
            raise ConfigError(f"Missing required config values: {', '.join(missing)}")


try:
    config = Config()
except ConfigError as e:
    print(f"Fatal error: {e}")
    exit(1)
