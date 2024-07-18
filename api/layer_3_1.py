# This is the easyest layer implemented
import os

# Only one user exist, logic without support database
# User can:

#   - view all file
#   - upload/download/delete/rename file

# nomeFile@Percorso@Visibilita

from layer_2 import TelegramAPI
from utils.response_handler import success, error
from utils.utils_functions import rename_file, move_file

ALL = "all"
VISIBLE = "visible"
NOT_VISIBLE = "not_visible"


class Layer3_1:
    def __init__(self):
        self.client = TelegramAPI()
        self.cluster_name = "Drive_Layer_3_1"
        self.base_directory = "./"
        self.trash_directory = self.base_directory + "trash"
        self.media_cache = None
        self.chat_id = self.__init_telegram_storage()

    # Check structure and recover chat id of cluster channel
    async def __init_telegram_storage(self):
        try:
            r = await self.client.get_chat_id_by_name(self.cluster_name)

            if r["status"] == "error":
                raise Exception(r['message'])

            # Cluster doesn't exist
            if r["data"] == 0:
                # You must create MANUALLY group in telegram chat -- api doesn't designed to do it
                raise Exception("Telegram chat group 'Drive_Layer_3_1' does not exist. Please create it manually.")
            else:
                return r["data"]

        except Exception as e:
            raise Exception(str(e))

    # Get all file and wrap it throw MEDIA object and memorized in cache
    async def __update_media_cache(self):
        r = await self.client.get_all_file_by_chatId(self.chat_id)
        if r["status"] == "error":
            return error(r["message"])
        self.media_cache = r["data"]
        return success("Media cache updated", None)

    # Get all files from the cache BY FILTER -- array MEDIA
    async def __get_all_file(self, FILTER):
        r = []
        if self.media_cache is None:
            self.media_cache = await self.__update_media_cache()
            if r["status"] == "error":
                raise Exception(r["message"])

        if FILTER == ALL:
            return self.media_cache
        else:
            for media in self.media_cache:
                if str(media.get_message_text()).split("@")[2] == FILTER:
                    r.append(media)
            return r

    # GET ACTION

    # Return list of text message attacked on each media present in the chat
    def get_al_media_message(self):
        result = []
        try:
            for media in self.__get_all_file(ALL):
                result.append(media.get_message_text())
        except Exception as e:
            return error(e)
        return success("Get successfully", result)

    # Return string list of all file's name present in the cluster
    def get_all_file_names(self):
        result = []
        try:
            for media in self.__get_all_file(ALL):
                result.append(str(media.get_message_text()).split("@")[0])
        except Exception as e:
            return error(e)
        return success("Get successfully", result)

    # Return unique set of directory available in the cluster
    def get_all_directory(self):
        result = set()
        try:
            for media in self.__get_all_file(ALL):
                result.add(str(media.get_message_text()).split("@")[1])
        except Exception as e:
            return error(e)
        return success("Get successfully", result)

    # Return media objects present in specific directory
    def get_all_media_by_directory(self, directory):
        result = []
        try:
            for media in self.__get_all_file(ALL):
                if str(media.get_media_name()).split("@")[1] == directory:
                    result.append(media)
        except Exception as e:
            return error(e)
        return success("Get successfully", result)

    def get_file_from_name(self, media_name):
        try:
            for media in self.__get_all_file(ALL):
                if str(media.get_message_text()).split("@")[0] == media_name:
                    return success("Get successfully", media)
        except Exception as e:
            return error(e)
        return error("File not found")



    # POST ACTION

    # Upload file to drive
    async def upload_file(self, src_file, scr_destination, visible):
        m = None
        try:
            m = os.path.basename(src_file) + "@" + scr_destination + "@" + visible
        except Exception as e:
            return error(e)
        response = await self.client.upload_file(self.chat_id, src_file, m)
        await self.__update_media_cache()
        return response

    # Rename file
    async def rename_file(self, old_name, new_name):

        m = self.get_file_from_name(old_name)
        if m["status"] == "error":
            return error(m["message"])
        response = await self.client.edit_message_by_message_instance(m["data"], rename_file(str(m["data"].get_message_text()).split("@")[0], new_name))
        await self.__update_media_cache()
        return response

    # Download file
    async def download_file(self, file_name, dest):
        m = self.get_file_from_name(file_name)
        if m["status"] == "error":
            return error(m["message"])
        response = await self.client.download_file_by_Media(m["data"], str(dest)+"/"+str(file_name))
        await self.__update_media_cache()
        return response

    # Move file from folder to another
    async def move_file(self, file_name, new_dest):
        m = self.get_file_from_name(file_name)
        if m["status"] == "error":
            return error(m["message"])
        response = await self.client.edit_message_by_message_instance(m["data"], move_file(str(m["data"].get_message_text()).split("@")[1], new_dest))
        await self.__update_media_cache()
        return response

    # Move to trash -- fake remove
    async def move_to_trash(self, file_name):
        return await self.move_file(file_name, self.trash_directory)

    # Remove definitive object from database
    async def delete_file(self, file_name):
        m = self.get_file_from_name(file_name)
        if m["status"] == "error":
            return error(m["message"])
        response = await self.delete_file(file_name)
        await self.__update_media_cache()
        return response

