from telethon.types import Message, MessageMediaDocument, MessageMediaPhoto


def bytes_to_mb(bytes):
    MB = bytes / (1024 * 1024)
    return round(MB, 2)


class Media:
    def __init__(self, id, text, mediaTelegram):
        self.id = str(id)
        self.text = str(text)
        self.mediaTelegram = mediaTelegram

    def __str__(self):
        return f"Media(id={self.id}, message={self.text}), mediaTelegram={self.mediaTelegram}"

    # Return id message
    def get_id_message(self):
        return self.id

    # Return text in the message
    def get_message_text(self):
        return self.text

    # Return media object telegram
    def get_mediaTelegram(self):
        return self.mediaTelegram

    # Return mime type of document
    def get_media_type(self):
        return self.get_mediaTelegram().document.mime_type

    # Return media size in MB
    def get_media_size(self):
        return bytes_to_mb(self.get_mediaTelegram().document.size)

    # Return media file name
    def get_media_name(self):
        return self.get_mediaTelegram().document.attributes[
            len(self.get_mediaTelegram().document.attributes) - 1].file_name

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
