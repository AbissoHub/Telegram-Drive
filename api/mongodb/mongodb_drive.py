import os
import re
from pymongo.errors import ConnectionFailure
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime

from utils.config import config
from utils.response_handler import success, error

VALID_FILE_NAME_REGEX = r'^[\w\-.]+$'


class DriveMongo:
    def __init__(self):
        self.url_mongo = None
        self.client = None
        self.db = None
        self.clusters_collection = None
        self.users_collection = None
        self.base_directory = "./"
        self.trash_directory = self.base_directory + "trash"

    # Init database
    def initialize_indexes(self):

        confirmation = input("Type 'CONFIRM' to initialize 'cluster-data': ")
        if confirmation != 'CONFIRM':
            print("[INFO] Initialization cancelled")
            return

        self.clusters_collection.drop()

        # INIT CLUSTER DATA
        self.clusters_collection.create_index("cluster_name")
        self.clusters_collection.create_index("cluster_id", unique=True)
        self.clusters_collection.create_index("files.is_folder")
        self.clusters_collection.create_index("files.id_message")
        self.clusters_collection.create_index("files.media_name")
        self.clusters_collection.create_index("files.locate_media")
        self.clusters_collection.create_index("files.media_size")
        self.clusters_collection.create_index("files.media_type")
        self.clusters_collection.create_index("files.date")

        print("[INFO] Initialization 'cluster-data' completed")

    # Sync data mongo_db -- telegram drive
    async def sync_data(self, layer):
        try:
            for cluster_name in layer.get_clusters_info():
                print(cluster_name)
                n = await layer.get_chat_id_by_name(cluster_name)
                # print(n)
                if n["status"] == "error":
                    return error(n["message"])

                cluster_id = n["data"]

                # Check if the cluster_id already exists in the database
                existing_cluster = self.clusters_collection.find_one({"cluster_id": cluster_id})
                if not existing_cluster:
                    print(f"[INFO] Creating cluster {cluster_name} with ID {cluster_id} in the database.")
                    # Insert new cluster if it does not exist
                    new_cluster = {
                        "cluster_id": cluster_id,
                        "cluster_name": cluster_name,
                        "files": []
                    }
                    self.clusters_collection.insert_one(new_cluster)

                r = await layer.get_all_file_by_cluster_id(cluster_name)
                if r["status"] == "error":
                    raise Exception(r['message'])

                for file in r["data"]:
                    # print(file)
                    #print(self.__get_file_by_id(file.get_id_message()))
                    if self.__get_file_by_id(file.get_id_message(), cluster_name) is None:
                        # Media not found in mongodb --> add media

                        # Create the new file document
                        new_file = {
                            "id_message": file.get_id_message(),
                            "media_name": file.get_media_name(),
                            "locate_media": file.get_locate_media(),
                            "media_size": file.get_media_size(),
                            "media_type": file.get_media_type(),
                            "message_text": file.get_message_text(),
                            "date": file.get_date(),
                            "is_folder": False
                        }

                        # Find the cluster and add the new file to the files array
                        self.clusters_collection.update_one(
                            {"cluster_name": cluster_name},
                            {"$push": {"files": new_file}}
                        )

                        print("[INFO] Media file added successfully")

            return success("Successfully sync data", None)
        except Exception as e:
            return error(f"Error sync data telegram-mongodb {e}")

    @classmethod
    async def create(cls, url, init):
        instance = cls()
        try:
            instance.client = MongoClient(url, server_api=ServerApi('1'))
            instance.db = instance.client[config.NAME_CLUSTER]
            instance.users_collection = instance.db["user-data"]
            instance.clusters_collection = instance.db["clusters-data"]

            print("[INFO] Connected to MongoDB")

            if init is True:
                try:
                    instance.initialize_indexes()
                except Exception as e:
                    print(f"[INFO] Error initializing database {e}")

        except ConnectionFailure as e:
            print(f"[ERROR] Could not connect to MongoDB: {e}")
            return None
        return instance

    # Get all discord_id
    def get_users_discord_id(self):
        cursor = self.users_collection.find({}, {"discord_id": 1, "_id": 0})
        discord_ids = [user['discord_id'] for user in cursor if 'discord_id' in user]
        return discord_ids

    # Get file by name and id
    def __get_file_by_id(self, file_id, cluster_name):
        result = self.clusters_collection.find_one(
            {"cluster_name": cluster_name, "files.id_message": file_id},
            {"files.$": 1}
        )
        return result["files"][0] if result else None

    # PUBLIC METHOD

    def get_trash_path(self):
        return self.trash_directory

    # Get file by id
    async def get_file_by_id(self, cluster_id, id_message):
        try:
            cluster = self.clusters_collection.find_one({"cluster_id": cluster_id})
            if not cluster:
                return error(f"Cluster with ID {cluster_id} not found")

            for file in cluster.get("files", []):
                if int(file.get("id_message")) == int(id_message):
                    return success("File found", file)

            return error("File not found")

        except Exception as e:
            return error(f"File does not exist {e}")

    async def get_all_files_by_cluster_id(self, cluster_id):
        try:
            result = self.clusters_collection.find_one(
                {"cluster_id": cluster_id},
                {"files": 1, "_id": 0}
            )
            if result and "files" in result:
                files = [file for file in result["files"] if file.get("locate_media") != "./trash"]
                if files:
                    for file in files:
                        file["cluster_id"] = cluster_id
                    return success("Get all files successfully", files)
                else:
                    return error("No files found after filtering")
            else:
                return error("Cluster does not exist or no files found")
        except Exception as e:
            return error(f"Error retrieving files for cluster {cluster_id}: {e}")

    async def get_all_files_trashed(self, cluster_id):
        try:
            result = self.clusters_collection.find_one(
                {"cluster_id": cluster_id},
                {"files": 1, "_id": 0}
            )
            if result and "files" in result:
                trashed_files = [file for file in result["files"] if file.get("locate_media") == "./trash"]
                if trashed_files:
                    for file in trashed_files:
                        file["cluster_id"] = cluster_id

                return success("Get all trashed files successfully", trashed_files)

            else:
                return error("Cluster does not exist or no files found")
        except Exception as e:
            return error(f"Error retrieving trashed files for cluster {cluster_id}: {e}")

    # Delete file from database
    async def delete_file(self, cluster_id, file_id):
        try:
            result = self.clusters_collection.update_one(
                {"cluster_id": int(cluster_id)},
                {"$pull": {"files": {"id_message": str(file_id)}}}
            )
            if result.modified_count > 0:
                return success("File deleted successfully", None)
            else:
                return error("File not found")
        except Exception as e:
            error(f"An error occurred while deleting the file: {e}")

    # Method to update file name and date
    async def update_file_name(self, cluster_id, file_id, new_name):
        try:

            # Check new name
            if not re.match(VALID_FILE_NAME_REGEX, new_name):
                return error("new name contains invalid characters")

            # Get current date and time
            current_date = datetime.utcnow()

            # Update the file name and date
            result = self.clusters_collection.update_one(
                {"cluster_id": int(cluster_id), "files.id_message": str(file_id)},
                {"$set": {
                    "files.$.media_name": new_name,
                    "files.$.date": current_date
                }}
            )
            if result.matched_count > 0:
                return success("File name updated successfully", None)
            else:
                return error("File not found")
        except Exception as e:
            return error(f"An error occurred while updating the file name: {e}")

    # Method to update file location
    async def update_file_location(self, cluster_id, file_id, new_location):
        try:
            result = self.clusters_collection.update_one(
                {"cluster_id": int(cluster_id), "files.id_message": str(file_id)},
                {"$set": {
                    "files.$.locate_media": new_location
                }}
            )
            if result.matched_count > 0:
                return success("File location updated successfully", None)
            else:
                return error("File not found")
        except Exception as e:
            error(f"An error occurred while updating the file location: {e}")

    # Trash file -- not delete
    async def trash_file(self, cluster_id, file_id):
        return await self.update_file_location(cluster_id, file_id, self.get_trash_path())

    async def create_folder(self, cluster_id, path_folder):
        try:
            existing_folder = self.clusters_collection.find_one(
                {"cluster_id": cluster_id, "files.locate_media": path_folder, "files.is_folder": True}
            )

            if existing_folder:
                return error("A folder with the same name already exists")

            file_data = {
                "id_message": -1,
                "media_name": "None",
                "locate_media": path_folder,
                "media_size": 0,
                "media_type": "None",
                "message_text": "None",
                "date": datetime.now(),
                "is_folder": True
            }

            result = self.clusters_collection.update_one(
                {"cluster_id": cluster_id},
                {"$push": {"files": file_data}}
            )

            if result.modified_count > 0:
                return success("Folder created successfully", None)
            else:
                return error("Cluster not found")

        except Exception as e:
            return error(f"An error occurred while inserting the folder: {e}")

    # Delete folder
    async def delete_folder(self, cluster_id, path_folder):
        try:
            result = self.clusters_collection.update_one(
                {"cluster_id": cluster_id},
                {"$pull": {"files": {"locate_media": path_folder, "is_folder": True}}}
            )
            if result.modified_count > 0:
                return success("Folder deleted successfully", None)
            else:
                return error("Cluster not found or folder not deleted")
        except Exception as e:
            return error(f"An error occurred while deleting the folder: {e}")

    # Rename folder
    async def rename_folder(self, cluster_id, old_path_folder, new_name):
        try:
            existing_folder = self.clusters_collection.find_one(
                {"cluster_id": cluster_id, "files.locate_media": old_path_folder, "files.is_folder": True}
            )

            if not existing_folder:
                return error("The folder does not exist with the given path")

            base_path = os.path.dirname(old_path_folder)
            new_path_folder = os.path.join(base_path, new_name)

            duplicate_folder = self.clusters_collection.find_one(
                {"cluster_id": cluster_id, "files.locate_media": new_path_folder, "files.is_folder": True}
            )

            if duplicate_folder:
                return error("A folder with the same name already exists at the new location")

            result = self.clusters_collection.update_one(
                {"cluster_id": cluster_id, "files.locate_media": old_path_folder, "files.is_folder": True},
                {"$set": {"files.$.locate_media": new_path_folder}}
            )

            if result.modified_count > 0:
                return success("Folder renamed successfully", None)
            else:
                return error("Folder not renamed, possibly cluster not found")

        except Exception as e:
            return error(f"An error occurred while renaming the folder: {e}")

    # Get all folders by cluster_id
    async def get_all_folders_by_cluster_id(self, cluster_id):
        try:
            result = self.clusters_collection.find_one(
                {"cluster_id": cluster_id},
                {"files": 1, "_id": 0}
            )
            if result and "files" in result:
                folders = [file for file in result["files"] if file["is_folder"]]
                return success("Get all folders successfully", folders)
            else:
                return error("Cluster does not exist or no folders found")
        except Exception as e:
            return error(f"Error retrieving folders for cluster {cluster_id}: {e}")

    # Get all files in a specific folder excluding subfolders
    async def get_files_in_folder(self, cluster_id, folder_path):
        try:
            result = self.clusters_collection.find_one(
                {"cluster_id": cluster_id},
                {"files": 1, "_id": 0}
            )
            if result and "files" in result:
                files = [file for file in result["files"]
                         if not file["is_folder"] and file["locate_media"] == folder_path]
                return success("Get all files in folder successfully", files)
            else:
                return error("Cluster or folder does not exist or no files found")
        except Exception as e:
            return error(f"Error retrieving files for folder {folder_path}: {e}")

    # Get all files in a specific folder including files in subfolders
    async def get_files_in_folder_including_subfolders(self, cluster_id, folder_path):
        try:
            result = self.clusters_collection.find_one(
                {"cluster_id": cluster_id},
                {"files": 1, "_id": 0}
            )
            if result and "files" in result:
                files = [file for file in result["files"]
                         if not file["is_folder"] and file["locate_media"].startswith(folder_path)]
                return success("Get all files in folder including subfolders successfully", files)
            else:
                return error("Cluster or folder does not exist or no files found")
        except Exception as e:
            return error(f"Error retrieving files for folder {folder_path} including subfolders: {e}")

    # Verifica se una cartella ha sottocartelle
    async def has_subfolders(self, cluster_id, folder_path):
        try:
            result = self.clusters_collection.find_one(
                {"cluster_id": cluster_id},
                {"files": 1, "_id": 0}
            )
            if result and "files" in result:
                subfolders = [
                    file for file in result["files"]
                    if file["is_folder"] and
                       file["locate_media"].startswith(folder_path.rstrip('/') + '/') and
                       file["locate_media"] != folder_path
                ]
                if subfolders:
                    return success("Subfolders found", True)
                else:
                    return success("Any Subfolders found", False)
            else:
                return error("Cluster or folder does not exist or no files found")
        except Exception as e:
            error(f"Error retrieving files for folder {folder_path} including subfolders: {e}")
