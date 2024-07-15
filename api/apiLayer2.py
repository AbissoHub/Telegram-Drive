from telethon import TelegramClient
from telethon.types import Message
from telethon.tl.types import InputMessagesFilterDocument
from utils.config import config
from utils.response_handler import success, error
import os
import functools
from format.Media import Media


# Printing download progress
def callback_download_progress(current, total):
    print('Downloaded', current, 'out of', total,
          'bytes: {:.2%}'.format(current / total))


def ensure_connected(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        if not self.is_connected():
            return error("Client is not connected")
        return await func(self, *args, **kwargs)

    return wrapper


class TelegramAPI:
    def __init__(self):
        self.API_ID = config.API_ID
        self.API_HASH = config.API_HASH
        self.PHONE = config.PHONE
        self.Name = "Telegram Drive"
        self.client = TelegramClient(self.Name, self.API_ID, self.API_HASH)

    def __get_API_ID(self):
        return self.API_ID

    def __get_API_HASH(self):
        return self.API_HASH

    def __get_PHONE(self):
        return self.PHONE

    def is_connected(self):
        return self.client.is_connected()

    async def connect(self):
        try:
            await self.client.start(self.__get_PHONE())
            if not self.is_connected():
                raise ConnectionError("Failed to connect to Telegram")
            return success("Client connected successfully", None)
        except Exception as e:
            return error(str(e))

    async def disconnect(self):
        try:
            if self.is_connected():
                await self.client.disconnect()
            return success("Client disconnected successfully", None)
        except Exception as e:
            return error(str(e))

    @ensure_connected
    async def get_chats(self):
        try:
            chats = []
            async for dialog in self.client.iter_dialogs():
                chats.append(dialog.name)
            return success("All chat fetched", chats)
        except Exception as e:
            return error(str(e))

    @ensure_connected
    async def get_chat_id_by_name(self, chat_name):
        try:
            async for dialog in self.client.iter_dialogs():
                if dialog.name == chat_name:
                    return success("Chat ID found", dialog.id)
            return error("Chat not found")
        except Exception as e:
            return error(str(e))

    # Fetch all message from specified 'chat_id' ( include file )
    # Return array of 'Message' object from telethon library
    @ensure_connected
    async def get_all_messages(self, chat_id):
        try:
            messages = []
            async for message in self.client.iter_messages(chat_id):
                messages.append(message)
                #print(message)
            # print(messages)
            return success("All messages fetched", messages)
        except Exception as e:
            return error(str(e))

    # Fetch all FILE MESSAGE from specified 'chat_id'
    # Return array of 'Media' object format/Media.py
    async def get_all_file_by_chatId(self, chat_id):
        result = []
        try:
            t = await self.get_all_messages(chat_id)
            if t["status"] == "error":
                return error(t['message'])

            for message in t['data']:
                if isinstance(message, Message) and message.file is not None:
                    # Format Media type
                    result.append(Media(message.id, message.message, message.media))
            # print(result[0].__str__())
            return success("All file fetched", result)

        except Exception as e:
            return error(str(e))

    # Fetch Specified file by message id - if doesn't exist return error
    # Return 'Media' object format/Media.py
    async def get_file_by_message_id(self, chat_id, message_id):
        try:
            t = await self.get_all_file_by_chatId(chat_id)
            if t["status"] == "error":
                return error(t['message'])

            for media in t['data']:
                if media.get_id() == str(message_id):
                    return success("File Exist", media)

            return error("File doesn't exist")
        except Exception as e:
            return error(str(e))


    # Download file by message_id and chat_id
    @ensure_connected
    async def download_file_by_message_id(self, chat_id, message_id, download_path):
        try:
            m = await self.get_file_by_message_id(chat_id, message_id)
            if m["status"] == "error":
                return error(m['message'])
            print(m["data"].get_mediaTelegram())
            await self.client.download_media(m["data"].get_mediaTelegram(), download_path, progress_callback=callback_download_progress)
            return success("File downloaded successfully", None)

        except Exception as e:
            return error(str(e))

    # Download file by Media object - format/Media.py
    @ensure_connected
    async def download_file_by_Media(self, m, download_path):
        try:
            await self.client.download_media(m, download_path,
                                             progress_callback=callback_download_progress)
            return success("File downloaded successfully", None)

        except Exception as e:
            return error(str(e))




    @ensure_connected
    async def upload_file(self, chat_id, file_path):
        try:
            await self.client.send_file(chat_id, file_path)
            return success("File uploaded successfully")
        except Exception as e:
            return error(str(e))

    @ensure_connected
    async def rename_file(self, chat_id, message_id, new_name):
        try:
            message = await self.client.get_messages(chat_id, ids=message_id)
            if message and message.file:
                old_path = await self.client.download_media(message, 'temp/')
                new_path = os.path.join(os.path.dirname(old_path), new_name)
                os.rename(old_path, new_path)
                await self.client.send_file(chat_id, new_path, caption="Renamed file")
                os.remove(new_path)
                return success("File renamed successfully")
            else:
                raise FileNotFoundError("File not found in the specified message")
        except Exception as e:
            return error(str(e))

    @ensure_connected
    async def delete_file(self, chat_id, message_id):
        try:
            await self.client.delete_messages(chat_id, message_id)
            return success("File deleted successfully")
        except Exception as e:
            return error(str(e))

    @ensure_connected
    async def send_message(self, chat_id, message):
        try:
            await self.client.send_message(chat_id, message)
            return success("Message sent successfully")
        except Exception as e:
            return error(str(e))

    @ensure_connected
    async def edit_message(self, chat_id, message_id, new_message):
        try:
            await self.client.edit_message(chat_id, message_id, new_message)
            return success("Message edited successfully")
        except Exception as e:
            return error(str(e))

    async def upload(self, file_path, target_group):
        try:
            file = await self.client.upload_file(file_path)
            await self.client.send_file(target_group, file)
            return success(f'File {file_path} uploaded to group {target_group}')
        except Exception as e:
            return error(str(e))

    async def download(self, target_group, target_file):
        try:
            async for message in self.client.iter_messages(target_group):
                if target_file in message.file.name:
                    path = await self.client.download_media(message, file=target_file)
                    return success(f'File downloaded to {path}')
            return error('File not found')
        except Exception as e:
            return error(str(e))

    async def delete(self, target_group, target_file):
        try:
            async for message in self.client.iter_messages(target_group):
                if target_file in message.file.name:
                    await self.client.delete_messages(target_group, [message.id])
                    return success(f'File {target_file} deleted from group {target_group}')
            return error('File not found')
        except Exception as e:
            return error(str(e))

    async def move(self, target_file, start_group, target_group):
        try:
            async for message in self.client.iter_messages(start_group):
                if target_file in message.file.name:
                    file_path = await self.client.download_media(message, file=target_file)
                    upload_response = await self.upload(file_path, target_group)
                    delete_response = await self.delete(start_group, target_file)
                    os.remove(file_path)
                    return success(f'File {target_file} moved from {start_group} to {target_group}')
            return error('File not found')
        except Exception as e:
            return error(str(e))

    async def rename(self, target_group, target_file, new_name):
        try:
            async for message in self.client.iter_messages(target_group):
                if target_file in message.file.name:
                    file_path = await self.client.download_media(message, file=target_file)
                    new_path = os.path.join(os.path.dirname(file_path), new_name)
                    os.rename(file_path, new_path)
                    upload_response = await self.upload(new_path, target_group)
                    delete_response = await self.delete(target_group, target_file)
                    os.remove(new_path)
                    return success(f'File {target_file} renamed to {new_name} in group {target_group}')
            return error('File not found')
        except Exception as e:
            return error(str(e))
