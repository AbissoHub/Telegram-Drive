import asyncio
from layer_2 import TelegramAPI

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


    print(response["data"][0])
    #response = await telegram_api.edit_message(response["data"][0].get_message_entity(), "ALO ALO ALO ALO")
    #print(response)

    response = await telegram_api.delete_file_by_id(-4231055711, 13399)
    print(response)

if __name__ == "__main__":
    asyncio.run(main())