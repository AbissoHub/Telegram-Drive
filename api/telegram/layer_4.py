import asyncio
import os
from format.Media import Media
from api.telegram.layer_3_2 import Layer3_2
from api.mongodb.mongodb_drive import DriveMongo
from utils.response_handler import success, error
from utils.config import config


class Layer4:
    def __init__(self):
        self.client = None
        self.mongo = None

    async def initialize(self):
        self.client = await Layer3_2.create()
        self.mongo = await DriveMongo().create(config.MONGO_URL, self.client, False)

    # ------------------------------------------------------------------------------------------

    # get mongo client
    def get_mongo_client(self):
        return self.mongo

    # Verify if client is connected -- OK
    def is_connect(self):
        return self.client.is_connected()

    # Connect client to telegram api -- OK
    async def connect(self):
        return await self.client.connect()

    # Close connection -- end
    async def disconnect(self):
        return await self.client.disconnect()

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

    # Get file info by cluster_id & file_id -- OK
    async def get_file_info(self, cluster_id, file_id):
        return await self.mongo.get_file_by_id(cluster_id, file_id)

    # Get file info by cluster_id & file_id -- OK
    async def get_file_trashed(self, cluster_id):
        r = await self.get_all_file(cluster_id)
        filtered_data = [file for file in r['data'] if './trash' in file['locate_media']]
        return success("Get Trashed Files", filtered_data)

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

    # Create folder -- OK
    async def create_folder(self, cluster_id, folder_path):
        return await self.get_mongo_client().create_folder(cluster_id, folder_path)

    # Create folder -- OK
    async def delete_folder(self, cluster_id, folder_path):
        # Get all file in folder
        r = await self.get_mongo_client().get_files_in_folder(cluster_id, folder_path)
        if len(r["data"] == 0):
            return error("Unable to delete folder that contains files")
        else:
            return await self.get_mongo_client().delete_folder(cluster_id, folder_path)

    # Rename folder
    async def rename_folder(self, cluster_id, old_path_folder, new_path_folder):
        return await self.get_mongo_client().rename_folder(cluster_id, old_path_folder, new_path_folder)

async def main():
    # Init layer4
    l = Layer4()
    await l.initialize()

    print(await l.get_all_file(4231055711))
    # print(await l.get_clusters_info())
    # print(await l.get_file_info(4231055711, 13528))
    # print(await l.sync_drive())

    # print(await l.create_folder(4231055711, "./aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"))

    print(await l.get_clusters_info())

    # print(await l.rename_file(4231055711, 13413, "pio.jpg"))
    # print(await l.move_file(4231055711, 13413, "./ciao"))
    # print(await l.move_to_trash(4231055711, 13413))

    # print(await l.delete_file(4231055711, 13413))
    # print(await l.upload_file("sample.pdf", "./test/upload", 4231055711))
    # print(await l.download_file(4231055711, 13528, "", "sample.pdf"))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
