from telethon.types import MessageMediaDocument


def bytes_to_mb(bytes):
    MB = bytes / (1024 * 1024)
    return round(MB, 2)


class Media:
    def __init__(self, message):

        self.id = str(message.id)
        self.message = message

    # Return message entity native of telethon
    def get_message_entity(self):
        return self.message

    # Return id message
    def get_id_message(self):
        return self.id

    # Return text in the message
    def get_message_text(self):
        return self.message.text

    # Return media object telegram
    def get_mediaTelegram(self):
        return self.message.media

    # Return mime type of document
    def get_media_type(self):
        return self.get_mediaTelegram().document.mime_type

    # Return media size in MB
    def get_media_size(self):
        return bytes_to_mb(self.get_mediaTelegram().document.size)

    # Return media file name -- THE ORIGINAL ONE
    def get_media_name_ORIGINAL(self):
        return self.get_mediaTelegram().document.attributes[
            len(self.get_mediaTelegram().document.attributes) - 1].file_name

    def get_media_name(self):
        return str(self.get_message_text()).split("@")[0]

    def get_locate_media(self):
        return str(self.get_message_text()).split("@")[1]

    # Return media 'date' object
    def get_date(self):
        return self.get_mediaTelegram().document.date

    def __str__(self):
        result = [
            f"ID Message: {self.get_id_message()}",
            f"Message Text: {self.get_message_text()}",
            f"Media Telegram: {self.get_mediaTelegram()}"
        ]
        if isinstance(self.get_mediaTelegram(), MessageMediaDocument):
            result.extend([
                f"Media Type: {self.get_media_type()}",
                f"Media Size (MB): {self.get_media_size()}",
                f"Media Name: {self.get_media_name()}"
            ])
        result.append(f"Date: {self.get_date()}")
        result.append(f"-----------------------------------------------")
        return '\n'.join(result)
