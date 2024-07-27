import asyncio
import os
from format.Media import Media
from layer_3_2 import Layer3_2
from mongodb import TelegramDriveMongo
from utils.response_handler import success, error
from utils.config import config


class Layer4:
    def __init__(self):
        self.client = None
        self.mongo = None

    async def initialize(self):
        self.client = await Layer3_2.create()
        self.mongo = await TelegramDriveMongo().create(config.MONGO_URL, self.client, False)

    # ------------------------------------------------------------------------------------------

    # Update method telegram - mongodb
    # Sync data from telegram drive to mongodb -- OK
    async def sync_drive(self):
        return await self.mongo.sync_data(self.client)

    # Get all cluster info -- OK
    async def get_clusters_info(self):
        return self.client.get_clusters_info()

    # Get all file by cluster_id -- OK
    async def get_all_file(self, cluster_id):
        return await self.mongo.get_all_files_by_cluster_id(cluster_id)

    async def get_file_info(self, cluster_id, file_id):
        return await self.mongo.get_file_by_id(cluster_id, file_id)

    # --------------------------------------------------------------------
    # --------------------------------------------------------------------
    # --------------------------------------------------------------------

    # Rename file -- OK
    async def rename_file(self, cluster_id, file_id, new_name):
        return await self.mongo.update_file_name(cluster_id, file_id, new_name)

    # Move file -- OK
    async def move_file(self, cluster_id, file_id, new_location):
        return await self.mongo.update_file_location(cluster_id, file_id, new_location)

    # Trash basket file -- OK
    async def move_to_trash(self, cluster_id, file_id):
        return await self.mongo.trash_file(cluster_id, file_id)

    # Delete file -- OK but the function doesn't return correctly ( + loop )
    async def delete_file(self, cluster_id, file_id):
        try:
            r1 = await self.mongo.delete_file(cluster_id, file_id)
            r2 = await self.client.delete_file(file_id, cluster_id)

            if r1['status'] == 'error':
                return error(r1["message"])
            elif r2['status'] == 'error':
                return error(r2["message"])
            else:
                return success("File deleted successfully", None)
        except Exception as e:
            return error(e)

    # Upload file -- OK but the function doesn't return correctly ( + loop )
    async def upload_file(self, src_file, scr_destination, cluster_id):
        # Upload
        try:
            r1 = await self.client.upload_file(src_file, scr_destination, cluster_id)
            if r1['status'] == 'error':
                return error(r1["message"])
            else:
                await self.sync_drive()
                return r1
        except Exception as e:
            return error(e)

    # Download file -- OK
    async def download_file(self, cluster_id, file_id, dest, name_file):
        try:
            r1 = await self.client.download_file(file_id, dest, cluster_id, name_file)
            return r1
        except Exception as e:
            return error(e)


async def main():
    # Init layer4
    l = Layer4()
    await l.initialize()

    print(await l.get_all_file(4231055711))
    print(await l.get_clusters_info())
    print(await l.get_file_info(4231055711, 13528))

    #print(await l.rename_file(4231055711, 13413, "pio.jpg"))
    #print(await l.move_file(4231055711, 13413, "./ciao"))
    #print(await l.move_to_trash(4231055711, 13413))

    #print(await l.delete_file(4231055711, 13413))
    #print(await l.upload_file("sample.pdf", "./test/upload", 4231055711))
    print(await l.download_file(4231055711, 13528, "", "sample.pdf"))

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
