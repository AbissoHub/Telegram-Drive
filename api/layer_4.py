import asyncio
import os
from format.Media import Media
from layer_3_2 import Layer3_2
from mongodb import TelegramDriveMongo
from utils.response_handler import success, error
from utils.utils_functions import rename_file, move_file, is_file_in_directory
from utils.config import config

class Layer4:
    def __init__(self):
        self.client = None
        self.mongo = None

    async def initialize(self):
        self.client = await Layer3_2.create()
        self.mongo = await TelegramDriveMongo().create(config.MONGO_URL, self.client)

    def get_mongo(self):
        return self.mongo

    def get_client(self):
        return self.client

async def main():
    l = Layer4()
    await l.initialize()

if __name__ == "__main__":
    asyncio.run(main())
