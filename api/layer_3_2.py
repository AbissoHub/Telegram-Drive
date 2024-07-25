# Multiple user available and supporting MongoDB to avoid multiple get requests
# User can't register, it is centralized, only admin can create credentials

# User have one gropchat associated as 'folder' structure to have low-level privacy
# Also there are gropchat open for everyUser to share file


# nomeFile@Percorso@Visibilita


import os
from format.Media import Media
from layer_2 import TelegramAPI
from utils.response_handler import success, error
from utils.utils_functions import rename_file, move_file, is_file_in_directory

ALL = "all"
VISIBLE = "visible"
NOT_VISIBLE = "not_visible"


class Layer3_2:
    def __init__(self):
        self.client = TelegramAPI()
        self.cluster_name_shared = "Drive_Layer_Shared"
        self.cluster_name_private = ["Drive_Layer_Shared"]
        self.base_directory = "./"
        self.trash_directory = self.base_directory + "trash"
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
                #print(self.shared_drive_object_dialog)
                # Init name of cluster private
                for id in self.client.get_users():
                    self.cluster_name_private.append("Drive_Layer_Private_" + str(id))
            return True
        except Exception as e:
            raise Exception(str(e))

    @classmethod
    async def create(cls):
        instance = cls()
        await instance.__init_telegram_storage()
        return instance

    # Get all cluster's private name
    def get_all_cluster_private_name(self):
        return self.cluster_name_private

    # Get chat id by name
    async def get_chat_id_by_name(self, cluster_name):
        r = await self.client.get_dialog_object_by_name(cluster_name)
        if r["status"] == "error":
            return error(r["message"])

        try:
            return success("Get chat id successfully", r["data"].draft.entity.id)
        except Exception as e:
            return error("Error getting chat id")


    # Get all files from private cluster
    async def get_all_file_in_private_cluster(self, FILTER, cluster_private_id):
        r = await self.client.get_all_file_by_chatId(cluster_private_id)
        if r["status"] == "error":
            return error(r["message"])

        if FILTER == ALL:
            return success("Get successfully ", r["data"])
        else:
            res = []
            for media in r["data"]:
                if str(media.get_message_text()).split("@")[2] == FILTER:
                    res.append(media)
            return success("Get successfully ", res)

    # Return list of text message attacked on each media present in the PRIVATE CLUSTER
    def get_all_text_message(self, medias):
        result = []
        try:
            for media in medias:
                result.append(media.get_message_text())
        except Exception as e:
            return error(e)
        return success("Get successfully", result)

    # Return string list of all file's name present in the cluster
    def get_all_file_names(self, medias):
        result = []
        try:
            for media in medias:
                result.append(str(media.get_message_text()).split("@")[0])
        except Exception as e:
            return error(e)
        return success("Get successfully", result)

    # Return unique set of directory available in the cluster
    def get_all_directory(self, media):
        result = set()
        try:
            for media in media:
                result.add(str(media.get_message_text()).split("@")[1])
        except Exception as e:
            return error(e)
        return success("Get successfully", result)

    # Return media objects present in specific directory
    def get_all_media_by_directory(self, medias, directory):
        result = []
        try:
            for media in medias:
                if str(media.get_message_text()).split("@")[1] == directory:
                    result.append(media)
        except Exception as e:
            return error(e)
        return success("Get successfully", result)

    # Return media objects present in specific directory
    def get_all_media_by_directory_incluse_subdir(self, directory, medias):
        result = []
        try:
            for media in medias:
                if is_file_in_directory(directory, str(media.get_message_text()).split("@")[1]):
                    result.append(media)
        except Exception as e:
            return error(e)
        return success("Get successfully", result)

    def get_file_by_name(self, media_name, medias):
        try:
            for media in medias:
                if str(media.get_message_text()).split("@")[0] == media_name:
                    return success("Get successfully", media)
        except Exception as e:
            return error(e)
        return error("File not found")

    async def get_file_by_id(self, message_id, medias):
        try:
            for media in medias:
                if str(media.get_id_message()) == str(message_id):
                    return success("Get successfully", media)
        except Exception as e:
            return error(e)
        return error("File not found")

    # POST ACTION

    # Upload file to drive - OK
    async def upload_file(self, src_file, scr_destination, visible, cluster_name):
        n = await self.client.get_dialog_object_by_name(cluster_name)
        if n["status"] == "error":
            return error(n["message"])

        m = None
        try:
            m = os.path.basename(src_file) + "@" + scr_destination + "@" + visible
        except Exception as e:
            return error(e)
        response = await self.client.upload_file(n["data"], src_file, m)
        return response

    # Rename file - OK
    async def rename_file(self, message_id, new_name, cluster_name):

        n = await self.client.get_dialog_object_by_name(cluster_name)
        if n["status"] == "error":
            return error(n["message"])

        m = await self.client.get_native_message_instance(n["data"], message_id)
        if m["status"] == "error":
            return error(m["message"])
        response = await self.client.edit_message_by_message_instance(m["data"], rename_file(
            str(Media(m["data"]).get_message_text()), new_name))
        return response

    # Download file
    async def download_file(self, message_id, dest, cluster_name):

        n = await self.client.get_dialog_object_by_name(cluster_name)
        if n["status"] == "error":
            return error(n["message"])

        m = await self.client.get_native_message_instance(n["data"], message_id)
        if m["status"] == "error":
            return error(m["message"])
        response = await self.client.download_file_by_Media(m["data"], str(dest) + Media(m["data"]).get_media_name())
        return response

    # Move file from folder to another - OK
    async def move_file(self, message_id, new_dest, cluster_name):

        n = await self.client.get_dialog_object_by_name(cluster_name)
        if n["status"] == "error":
            return error(n["message"])

        m = await self.client.get_native_message_instance(n["data"], message_id)
        if m["status"] == "error":
            return error(m["message"])
        response = await self.client.edit_message_by_message_instance(m["data"], move_file(
            str(Media(m["data"]).get_message_text()), new_dest))
        return response

    # Move to trash -- fake remove - OK
    async def move_to_trash(self, message_id, cluster_name):
        return await self.move_file(message_id, self.trash_directory, cluster_name)

    # Remove definitive object from database - OK
    async def delete_file(self, message_id, cluster_name):
        n = await self.client.get_dialog_object_by_name(cluster_name)
        if n["status"] == "error":
            return error(n["message"])

        m = await self.client.get_native_message_instance(n["data"], message_id)
        if m["status"] == "error":
            return error(m["message"])
        response = await self.client.delete_file_by_message_instance(m["data"])
        return response
