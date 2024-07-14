from telethon import TelegramClient
from telethon.tl.types import InputMessagesFilterDocument
from utils.config import config
from utils.response_handler import success, error
import os
import functools


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
            return success("Client connected successfully")
        except Exception as e:
            return error(str(e))

    async def disconnect(self):
        try:
            if self.is_connected():
                await self.client.disconnect()
            return success("Client disconnected successfully")
        except Exception as e:
            return error(str(e))

    @ensure_connected
    async def get_chats(self):
        try:
            chats = []
            async for dialog in self.client.iter_dialogs():
                chats.append(dialog.name)
            return success(chats)
        except Exception as e:
            return error(str(e))

    @ensure_connected
    async def get_chat_id_by_name(self, chat_name):
        try:
            async for dialog in self.client.iter_dialogs():
                if dialog.name == chat_name:
                    return success(dialog.id)
            return error("Chat not found")
        except Exception as e:
            return error(str(e))

    @ensure_connected
    async def get_messages(self, chat_id):
        try:
            messages = []
            async for message in self.client.iter_messages(chat_id):
                messages.append(message.to_dict())
                print(message)
            return success(messages)
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
    async def download_file(self, chat_id, message_id, download_path):
        try:
            message = await self.client.get_messages(chat_id, ids=message_id)
            if message and message.file:
                await self.client.download_media(message, download_path)
                return success("File downloaded successfully")
            else:
                raise FileNotFoundError("File not found in the specified message")
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
