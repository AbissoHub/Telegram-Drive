# This is the easyest layer implemented

# Only one user exist, logic without support database
# User can:

#   - view all file
#   - upload/download/delete/rename file

# nomeFile@Percorso@Visibilita

# no longer maintained -- for illustrative purposes only

import os
from format.Media import Media
from layer_2 import TelegramAPI
from utils.response_handler import success, error
from utils.utils_functions import rename_file, move_file, is_file_in_directory

ALL = "all"
VISIBLE = "visible"
NOT_VISIBLE = "not_visible"


class Layer3_1:
    def __init__(self):
        self.client = TelegramAPI()
        self.cluster_name = "Drive_Layer_3_1"
        self.base_directory = "./"
        self.trash_directory = self.base_directory + "trash"
        self.chat_id = None

    async def __init_telegram_storage(self):
        try:
            # Connect telegram
            s = await self.client.connect()
            print(s)
            r = await self.client.get_chat_id_by_name(self.cluster_name)

            if r["status"] == "error":
                raise Exception(r['message'])

            # Cluster doesn't exist
            if r["data"] == 0:
                # You must create MANUALLY group in telegram chat -- api doesn't designed to do it
                raise Exception("Telegram chat group 'Drive_Layer_3_1' does not exist. Please create it manually.")
            else:
                self.chat_id = r["data"]

            return True

        except Exception as e:
            raise Exception(str(e))

    @classmethod
    async def create(cls):
        instance = cls()
        await instance.__init_telegram_storage()
        return instance

    # Get all files BY FILTER -- array MEDIA
    async def __get_all_file(self, FILTER):
        r = await self.client.get_all_file_by_chatId(self.chat_id)
        if r["status"] == "error":
            return error(r["message"])

        if FILTER == ALL:
            return r["data"]
        else:
            for media in r["data"]:
                if str(media.get_message_text()).split("@")[2] == FILTER:
                    r.append(media)
            return r

    # GET ACTION

    # Return list of text message attacked on each media present in the chat
    async def get_all_text_message(self):
        result = []
        try:
            for media in await self.__get_all_file(ALL):
                result.append(media.get_message_text())
        except Exception as e:
            return error(e)
        return success("Get successfully", result)

    # Return string list of all file's name present in the cluster
    async def get_all_file_names(self):
        result = []
        try:
            for media in await self.__get_all_file(ALL):
                result.append(str(media.get_message_text()).split("@")[0])
        except Exception as e:
            return error(e)
        return success("Get successfully", result)

    # Return unique set of directory available in the cluster
    async def get_all_directory(self):
        result = set()
        try:
            for media in await self.__get_all_file(ALL):
                result.add(str(media.get_message_text()).split("@")[1])
        except Exception as e:
            return error(e)
        return success("Get successfully", result)

    # Return media objects present in specific directory
    async def get_all_media_by_directory(self, directory):
        result = []
        try:
            for media in await self.__get_all_file(ALL):
                if str(media.get_message_text()).split("@")[1] == directory:
                    result.append(media)
        except Exception as e:
            return error(e)
        return success("Get successfully", result)

    # Return media objects present in specific directory
    async def get_all_media_by_directory_incluse_subdir(self, directory):
        result = []
        try:
            for media in await self.__get_all_file(ALL):
                if is_file_in_directory(directory, str(media.get_message_text()).split("@")[1]):
                    result.append(media)
        except Exception as e:
            return error(e)
        return success("Get successfully", result)

    async def get_file_by_name(self, media_name):
        try:
            for media in await self.__get_all_file(ALL):
                if str(media.get_message_text()).split("@")[0] == media_name:
                    return success("Get successfully", media)
        except Exception as e:
            return error(e)
        return error("File not found")

    async def get_file_by_id(self, message_id):
        try:
            for media in await self.__get_all_file(ALL):
                if str(media.get_id_message()) == str(message_id):
                    return success("Get successfully", media)
        except Exception as e:
            return error(e)
        return error("File not found")

    # POST ACTION

    # Upload file to drive - OK
    async def upload_file(self, src_file, scr_destination, visible):
        m = None
        try:
            m = os.path.basename(src_file) + "@" + scr_destination + "@" + visible
        except Exception as e:
            return error(e)
        response = await self.client.upload_file(self.chat_id, src_file, m)
        return response

    # Rename file - OK
    async def rename_file(self, message_id, new_name):

        m = await self.client.get_native_message_instance(self.chat_id, message_id)
        if m["status"] == "error":
            return error(m["message"])
        response = await self.client.edit_message_by_message_instance(m["data"], rename_file(
            str(Media(m["data"]).get_message_text()), new_name))
        return response

    # Download file
    async def download_file(self, message_id, dest):
        m = await self.client.get_native_message_instance(self.chat_id, message_id)
        if m["status"] == "error":
            return error(m["message"])
        response = await self.client.download_file_by_Media(m["data"], str(dest) + Media(m["data"]).get_media_name())
        return response

    # Move file from folder to another - OK
    async def move_file(self, message_id, new_dest):
        m = await self.client.get_native_message_instance(self.chat_id, message_id)
        if m["status"] == "error":
            return error(m["message"])
        response = await self.client.edit_message_by_message_instance(m["data"], move_file(
            str(Media(m["data"]).get_message_text()), new_dest))
        return response

    # Move to trash -- fake remove - OK
    async def move_to_trash(self, message_id):
        return await self.move_file(message_id, self.trash_directory)

    # Remove definitive object from database - OK
    async def delete_file(self, message_id):
        m = await self.client.get_native_message_instance(self.chat_id, message_id)
        if m["status"] == "error":
            return error(m["message"])
        response = await self.client.delete_file_by_message_instance(m["data"])
        return response
