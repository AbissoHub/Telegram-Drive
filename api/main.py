import asyncio
from layer_3_1 import Layer3_1


async def main():
    endpoint = await Layer3_1.create()

    # Get all media messages
    response = await endpoint.get_all_text_message()
    print(response)

    # Get all file names
    response = await endpoint.get_all_file_names()
    print(response)

    # Get all directories
    response = await endpoint.get_all_directory()
    print(response)

    # Get all media by directory
    response = await endpoint.get_all_media_by_directory("./")
    print(response)

    # Upload file
    #response = await endpoint.upload_file("./test.jpg", "./", "all")
    #print(response)

    # Get file from name
    response = await endpoint.get_file_by_name("ano.jpg")
    print(response)

    # Rename file
    #response = await endpoint.rename_file(response["data"].get_id_message(), "ano1.jpg")
    #print(response)

    # Move file
    #response = await endpoint.move_to_trash(response["data"].get_id_message())
    #print(response)

    response = await endpoint.get_all_media_by_directory_incluse_subdir("./giacomo")
    print(response)
    # Download file
    # response = await endpoint.download_file(response["data"].get_id_message(), "./")
    # print(response)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

