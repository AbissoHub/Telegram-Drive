# Multiple user available and supporting MongoDB to avoid multiple get requests
# User can't register, it is centralized, only admin can create credentials

# User have one gropchat associated as 'folder' structure to have low-level privacy
# Also there are gropchat open for everyUser to share file

# Telegram is used by layer to store data and not organised metadata. Only folder logic is implemented in layer

import os
from format.Media import Media
from layer_2 import TelegramAPI
from utils.response_handler import success, error
from utils.utils_functions import rename_file, move_file, is_file_in_directory


class Layer3_2:
    def __init__(self):
        self.client = TelegramAPI()
        self.cluster_name_shared = "Drive_Layer_Shared"
        self.clusters_info = {}
        self.shared_drive_object_dialog = None

    async def __init_telegram_storage(self):
        try:
            # Connect telegram
            s = await self.client.connect()
            print(s)
            r = await self.client.get_dialog_object_by_name(self.cluster_name_shared)

            if r["status"] == "error":
                raise Exception(r['message'])

            # Cluster doesn't exist
            if r["data"] == 0:
                # You must create MANUALLY group in telegram chat -- api doesn't designed to do it
                raise Exception("Telegram chat group 'Drive_Layer_Shared' does not exist. Please create it manually.")
            else:
                self.shared_drive_object_dialog = r["data"]
                self.clusters_info["Drive_Layer_Shared"] = str(
                    self.shared_drive_object_dialog.draft.entity.id)
                # print(self.shared_drive_object_dialog)
                # Init name of cluster private
                for n in self.client.get_users():
                    name = "Drive_Layer_Private_" + str(n)
                    #GET ID
                    r = await self.client.get_dialog_object_by_name(name)
                    if r["status"] == "error":
                        raise Exception(r['message'])
                    self.clusters_info[name] = str(r["data"].draft.entity.id)
            return True

        except Exception as e:
            raise Exception(str(e))

    @classmethod
    async def create(cls):
        instance = cls()
        await instance.__init_telegram_storage()
        return instance

    # Get json clusters info (private and shared)
    def get_clusters_info(self):
        return self.clusters_info

    # Get chat id by name
    async def get_chat_id_by_name(self, cluster_name):
        r = await self.client.get_dialog_object_by_name(cluster_name)
        if r["status"] == "error":
            return error(r["message"])
        try:
            return success("Get chat id successfully", r["data"].draft.entity.id)
        except Exception as e:
            return error(f"[LAYER-3] Error getting chat id: {e}")

    # Get all files from private cluster
    async def get_all_file_by_cluster_id(self, cluster_id):
        r = await self.client.get_all_file_by_chatId(cluster_id)
        if r["status"] == "error":
            return error(r["message"])

        try:
            res = []
            for media in r["data"]:
                res.append(media)
            return success("Get successfully ", res)

        except Exception as e:
            return error(f"[LAYER-3] Error getting files: {e}")

    # POST ACTION

    # Upload file to drive -
    async def upload_file(self, src_file, scr_destination, cluster_id):
        n = await self.client.get_dialog_object_by_id(cluster_id)
        if n["status"] == "error":
            return error(n["message"])

        m = None
        try:
            m = os.path.basename(src_file) + "@" + scr_destination
        except Exception as e:
            return error("[LAYER-3] " + str(e))
        response = await self.client.upload_file(n["data"], src_file, m)
        return response

    # Download file -
    async def download_file(self, message_id, dest, cluster_id, media_name):

        n = await self.client.get_dialog_object_by_id(cluster_id)
        if n["status"] == "error":
            return error(n["message"])

        m = await self.client.get_native_message_instance(n["data"], message_id)
        if m["status"] == "error":
            return error(m["message"])
        response = await self.client.download_file_by_Media(m["data"], str(dest) + media_name)
        return response

    # Remove definitive object from database -
    async def delete_file(self, message_id, cluster_id):

        n = await self.client.get_dialog_object_by_id(cluster_id)
        if n["status"] == "error":
            return error(n["message"])

        m = await self.client.get_native_message_instance(n["data"], message_id)
        if m["status"] == "error":
            return error(m["message"])
        response = await self.client.delete_file_by_message_instance(m["data"])
        return response
