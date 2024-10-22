from telethon import TelegramClient
from telethon.tl.functions.channels import CreateChannelRequest, CheckUsernameRequest, UpdateUsernameRequest
from telethon.errors import UsernameInvalidError, UsernameOccupiedError
from telethon.types import Message
from utils.config import config
from utils.response_handler import success, error
import functools
from format.Media import Media


# Printing download progress
def callback_download_progress(current, total):
    print('Download', current, 'out of', total, 'bytes: {:.2%}'.format(current / total))


# Printing upload progress
def callback_upload_progress(current, total):
    print('Upload', current, 'out of', total, 'bytes: {:.2%}'.format(current / total))


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
            return error("[LAYER-2]" + str(e))

    async def disconnect(self):
        try:
            if self.is_connected():
                await self.client.disconnect()
            return success("Client disconnected successfully", None)
        except Exception as e:
            return error("[LAYER-2]" + str(e))

    @ensure_connected
    async def get_chats(self):
        """Fetch all chat names."""
        try:
            chats = []
            async for dialog in self.client.iter_dialogs():
                chats.append(dialog.name)
            return success("All chats fetched", chats)
        except Exception as e:
            return error("[LAYER-2]" + str(e))

    @ensure_connected
    async def get_dialog_object_by_name(self, chat_name):
        """Fetch dialog object (telethon object) by chat name."""
        try:
            async for dialog in self.client.iter_dialogs():
                if str(dialog.name) == str(chat_name):
                    return success("Dialog object found", dialog)
            return success("[LAYER-2] Dialog object not found", None)
        except Exception as e:
            return error(str(e))

    @ensure_connected
    async def get_dialog_object_by_id(self, chat_id):
        """Fetch dialog object (telethon object) by chat name."""
        try:
            async for dialog in self.client.iter_dialogs():
                if int(dialog.draft.entity.id) == int(chat_id):
                    return success("Dialog object found", dialog)
            return error("[LAYER-2] Dialog object not found")
        except Exception as e:
            return error(str(e))

    @ensure_connected
    async def get_all_messages(self, chat_id):
        """Fetch all messages from a chat."""
        try:
            messages = []
            async for message in self.client.iter_messages(chat_id):
                messages.append(message)
            return success("All messages fetched", messages)
        except Exception as e:
            return error("[LAYER-2] " + str(e))

    async def get_all_file_by_chatId(self, chat_id):
        """Fetch all file messages from a chat."""
        result = []
        try:
            t = await self.get_all_messages(chat_id)
            if t["status"] == "error":
                return error("[LAYER-2] " + t['message'])

            for message in t['data']:
                if isinstance(message, Message) and message.file is not None:
                    result.append(Media(message))
            return success("All files fetched", result)
        except Exception as e:
            return error("[LAYER-2] " + str(e))

    async def get_native_message_instance(self, chat_id, message_id):
        """Fetch native message instance from a chat by message_id."""
        try:
            t = await self.get_all_messages(chat_id)
            if t["status"] == "error":
                return error("[LAYER-2] " + t['message'])

            for message in t['data']:
                if isinstance(message, Message) and message.file is not None:
                    if str(message.id) == str(message_id):
                        return success("Message fetched", message)
            return error("[LAYER-2] Message not found")
        except Exception as e:
            return error("[LAYER-2] " + str(e))

    async def get_file_by_message_id(self, chat_id, message_id):
        """Fetch a specific file by message ID."""
        try:
            t = await self.get_all_file_by_chatId(chat_id)
            if t["status"] == "error":
                return error("[LAYER-2] " + t['message'])

            for media in t['data']:
                if str(media.get_id_message()) == str(message_id):
                    return success("File exists", media)
            return error("[LAYER-2] File doesn't exist")
        except Exception as e:
            return error("[LAYER-2] " + str(e))

    @ensure_connected
    async def download_file_by_message_id(self, chat_id, message_id, download_path):
        """Download file by message ID."""
        try:
            m = await self.get_file_by_message_id(chat_id, message_id)
            if m["status"] == "error":
                return error("[LAYER-2] " + m['message'])
            await self.client.download_media(m["data"].get_mediaTelegram(), download_path,
                                             progress_callback=callback_download_progress)
            return success("File downloaded successfully", None)
        except Exception as e:
            return error("[LAYER-2] " + str(e))

    @ensure_connected
    async def download_file_by_Media(self, m):
        """Download file by Media object."""
        try:
            async def async_data_generator():
                async for chunk in self.client.iter_download(m):
                    yield chunk

            return success("File downloaded successfully", async_data_generator)
        except Exception as e:
            return error("[LAYER-2] " + str(e))

    async def iter_download_file_by_Media(self, media, chunk_size=8192):
        async for chunk in self.client.iter_download(media, chunk_size=chunk_size):
            yield chunk

    @ensure_connected
    async def upload_file(self, chat, file_storage, message, file_size):
        try:
            input_file = await self.client.upload_file(
                file=file_storage.stream,
                file_size=file_size,
                file_name=file_storage.filename
            )

            await self.client.send_file(
                chat,
                file=input_file,
                caption=message,
                force_document=True
            )
            return {'status': 'success', 'message': "File caricato con successo"}
        except Exception as e:
            return {'status': 'error', 'message': "[LAYER-2] " + str(e)}

    @ensure_connected
    async def edit_message_by_message_instance(self, mess, new_message):
        """Edit a message by chat ID and message ID."""
        try:
            t = await self.client.edit_message(mess, new_message)
            # print(t)
            if str(t.message) == str(new_message):
                return success("Message edited successfully", None)
        except Exception as e:
            return error("[LAYER-2] " + str(e))

    @ensure_connected
    async def delete_file_by_message_instance(self, mess):
        """Delete a file by message instance."""
        try:
            await mess.delete()
            return success("File deleted successfully", None)
        except Exception as e:
            return error("[LAYER-2] " + str(e))

    @ensure_connected
    async def create_group(
            self,
            title: str,
            about: str = "",
            megagroup: bool = False,
    ) -> dict:
        """
        Creates a new group on Telegram.
        """
        try:
            # Create the channel/group
            result = await self.client(CreateChannelRequest(
                title=title,
                about=about,
                megagroup=megagroup
            ))
            channel = result.chats[0]

            return success({
                "id": channel.id,
                "title": channel.title,
                "access_hash": channel.access_hash
            }, None)

        except Exception as e:
            return error(f"Error creating the group: {e}")

