# Module to interact with mongodb api:
# - login / create valide session multi user telegram
import asyncio
import uuid
from pymongo.errors import ConnectionFailure
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import datetime
from utils.response_handler import success, error

ALL = "all"
VISIBLE = "visible"
NOT_VISIBLE = "not_visible"


class TelegramDriveMongo:
    def __init__(self):
        self.url_mongo = None
        self.client = None
        self.db = None
        self.users_collection = None
        self.clusters_collection = None

    # Init database
    def initialize_indexes(self):

        confirmation = input("Type 'CONFIRM' to initialize 'cluster-data': ")
        if confirmation != 'CONFIRM':
            print("[INFO] Initialization cancelled")
            return

        self.clusters_collection.drop()

        # INIT CLUSTER DATA
        self.users_collection.create_index("cluster_name")
        self.users_collection.create_index("cluster_id", unique=True)
        self.users_collection.create_index("files.id_message")
        self.users_collection.create_index("files.media_name")
        self.users_collection.create_index("files.locate_media")
        self.users_collection.create_index("files.media_size")
        self.users_collection.create_index("files.media_type")
        self.users_collection.create_index("files.message_text")
        self.users_collection.create_index("files.date")

        print("[INFO] Initialization 'cluster-data' completed")

    # Sync data mongo_db -- telegram drive
    async def __sync_data(self, layer):
        for cluster_name in layer.get_all_cluster_private_name():

            n = await layer.get_chat_id_by_name(cluster_name)
            if n["status"] == "error":
                return error(n["message"])

            cluster_id = n["data"]

            # Check if the cluster_id already exists in the database
            existing_cluster = self.clusters_collection.find_one({"cluster_id": cluster_id})
            if not existing_cluster:
                print(f"[INFO] Cluster {cluster_name} with ID {cluster_id} already exists in the database.")
                # Insert new cluster if it does not exist
                new_cluster = {
                    "cluster_id": cluster_id,
                    "cluster_name": cluster_name,
                    "files": []
                }
                self.clusters_collection.insert_one(new_cluster)

            r = await layer.get_all_file_in_private_cluster(ALL, cluster_name)
            if r["status"] == "error":
                raise Exception(r['message'])

            for file in r["data"]:
                print(file)
                if self.__get_file_by_name_and_id(file.get_media_name(), file.get_id_message()) is None:
                    # Media not found in mongodb --> add media

                    # Create the new file document
                    new_file = {
                        "id_message": file.get_id_message(),
                        "media_name": file.get_media_name(),
                        "locate_media": file.get_locate_media(),
                        "media_size": file.get_media_size(),
                        "media_type": file.get_media_type(),
                        "message_text": file.get_message_text(),
                        "date": file.get_date()
                    }

                    # Find the cluster and add the new file to the files array
                    self.clusters_collection.update_one(
                        {"cluster_name": cluster_name},
                        {"$push": {"files": new_file}}
                    )

                    print("[INFO] Media file added successfully")

    @classmethod
    async def create(cls, url, layer):
        instance = cls()
        try:
            instance.client = MongoClient(url, server_api=ServerApi('1'))
            instance.db = instance.client['Teledrive']
            instance.users_collection = instance.db["user-data"]
            instance.clusters_collection = instance.db["clusters-data"]
            print("[INFO] Connected to MongoDB")

            #instance.initialize_indexes()

        except ConnectionFailure as e:
            print(f"[ERROR] Could not connect to MongoDB: {e}")
            return None
        await instance.__sync_data(layer)
        return instance

    # Return user object using discord id
    def __get_user_by_discord_id(self, discord_id):
        result = self.users_collection.find_one({"discord_id": discord_id})
        return result

    # Get user by username
    def __get_user_by_username(self, username):
        result = self.users_collection.find_one({"username": username})
        return result

    # Get all discord_ids
    def __get_all_discord_ids(self):
        discord_ids = self.users_collection.distinct("discord_id")
        return discord_ids

    # Get all files by cluster_name
    def __get_all_files_by_cluster_name(self, cluster_name):
        files = self.clusters_collection.find_one({"cluster_name": cluster_name})
        return files

    # Get file by name and id
    def __get_file_by_name_and_id(self, name, file_id):
        result = self.clusters_collection.find_one(
            {"files": {"$elemMatch": {"id": file_id, "name": name}}},
            {"files.$": 1}
        )
        if result and "files" in result:
            return result["files"][0]
        return None

    # PUBLIC METHOD

    # Get file by name
    def get_file_by_id(self, cluster_name, id):
        try:
            result = self.clusters_collection.find_one(
                {"cluster_name": cluster_name, "files.id_message": id},
                {"files.$": 1}
            )
            if result and "files" in result:
                success("Get file successfully", result["files"][0])
            else:
                error("File does not exist")
        except Exception as e:
            error(f"File does not exist {e}")

    # Delete file from database
    def delete_file(self, cluster_name, file_id):
        try:
            result = self.clusters_collection.update_one(
                {"cluster_name": cluster_name},
                {"$pull": {"files": {"id_message": file_id}}}
            )
            if result.modified_count > 0:
                success("File deleted successfully")
            else:
                error("File not found")
        except Exception as e:
            error(f"An error occurred while deleting the file: {e}")

    # Method to update file name
    def update_file_name(self, cluster_name, file_id, new_name):
        try:
            result = self.clusters_collection.update_one(
                {"cluster_name": cluster_name, "files.id_message": file_id},
                {"$set": {
                    "files.$.media_name": new_name
                }}
            )
            if result.matched_count > 0:
                success("File name updated successfully")
            else:
                error("File not found")
        except Exception as e:
            error(f"An error occurred while updating the file name: {e}")

    # Method to update file location
    def update_file_location(self, cluster_name, file_id, new_location):
        try:
            result = self.clusters_collection.update_one(
                {"cluster_name": cluster_name, "files.id_message": file_id},
                {"$set": {
                    "files.$.locate_media": new_location
                }}
            )
            if result.matched_count > 0:
                success("File location updated successfully")
            else:
                error("File not found")
        except Exception as e:
            error(f"An error occurred while updating the file location: {e}")
