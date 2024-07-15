# Include id message,
class Media:
    def __init__(self, id, text, mediaTelegram):
        self.id = str(id)
        self.text = str(text)
        self.mediaTelegram = mediaTelegram

    def __str__(self):
        return f"Media(id={self.id}, message={self.text}), mediaTelegram={self.mediaTelegram}"

    def get_id(self):
        return self.id

    def get_message(self):
        return self.text

    def get_mediaTelegram(self):
        return self.mediaTelegram
