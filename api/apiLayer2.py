from telethon import TelegramClient
from utils.config import config
from utils.response_handler import success, error
import os


class TelegramAPI:
    def __init__(self):

        self.API_ID = config('API_ID')
        self.API_HASH = config('API_HASH')
        self.PHONE = config('PHONE')
        self.Name = "Telegram Drive"
        self.client = TelegramClient(self.Name, self.API_ID, self.API_HASH)

    def __get_API_ID(self):
        return self.API_ID

    def __get_API_HASH(self):
        return self.API_HASH

    def __get_PHONE(self):
        return self.PHONE

    def __is_connected(self):
        return self.client.is_connected()

    async def connect(self, phone):
        try:
            await self.client.start(phone)
            if not self.__is_connected():
                raise ConnectionError("Failed to connect to Telegram")
            return success("Client connected successfully")
        except Exception as e:
            return error(str(e))

    async def disconnect(self):
        try:
            await self.client.disconnect()
            return success("Client disconnected successfully")
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
