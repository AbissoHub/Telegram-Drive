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
    response = await endpoint.get_all_media_by_directory("./giacomo/home/uni")
    print(response)

    # Get file from name
    response = await endpoint.get_file_from_name("Luke.jpg")
    print(response)

    # Upload file
    response = await endpoint.upload_file("./test.jpg", "./", "all")
    print(response)

    # Rename file
    response = await endpoint.rename_file("Luke.jpg", "test_renamed.jpg")
    print(response)

    # Download file
    #response = await endpoint.download_file("test_renamed.png", "path/to/download_directory")
    #print(response)




if __name__ == "__main__":
    asyncio.run(main())
