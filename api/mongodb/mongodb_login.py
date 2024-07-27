# Module to interact with mongodb api to login
# - register isn't allowed, only admin can register new user

import asyncio
import uuid
from pymongo.errors import ConnectionFailure
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
from utils.config import config
from utils.response_handler import success, error


class TelegramDriveMongo:
    def __init__(self):
        self.url_mongo = config.MONGO_URL
        self.client = MongoClient(self.url_mongo, server_api=ServerApi('1'))
        self.db = self.client['Teledrive']
        self.users_collection = self.db["user-data"]

    # Init database
    def initialize_indexes(self):

        confirmation = input("Type 'CONFIRM' to initialize 'cluster-data': ")
        if confirmation != 'CONFIRM':
            print("[INFO] Initialization cancelled")
            return

        self.users_collection.drop()

        # INIT CLUSTER DATA
        self.users_collection.create_index("cluster_name")
        self.users_collection.create_index("cluster_id", unique=True)

        print("[INFO] Initialization 'cluster-data' completed")
