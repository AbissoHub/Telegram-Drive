import asyncio
from apiLayer2 import TelegramAPI

async def main():
    telegram_api = TelegramAPI()

    # Connect to Telegram
    response = await telegram_api.connect()
    print(response)

    # Get all chats
    response = await telegram_api.get_chats()
    print(response)

    response = await telegram_api.get_chat_id_by_name("123456789")
    print(response)

    response = await telegram_api.get_all_file_by_chatId(-4231055711)
    print(response)

    #response = await telegram_api.rename_file(-4231055711, 13399, "ANO1")
    #print(response)

if __name__ == "__main__":
    asyncio.run(main())