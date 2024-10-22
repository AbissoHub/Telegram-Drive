import asyncio
from api.telegram.layer_3_2 import Layer3_2
from api.mongodb.mongodb_drive import DriveMongo
from utils.response_handler import success, error
from utils.config import config


class Layer4:
    def __init__(self):
        self.client = None
        self.mongo = None

    async def initialize(self):
        self.mongo = await DriveMongo().create(config.MONGO_URL, False)
        self.client = await Layer3_2.create(self.mongo.get_users_discord_id())
        await self.mongo.sync_data(self.client)

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

    # Get trashed files -- OK
    async def get_file_trashed(self):
        r = await self.get_clusters_info()
        all_data = []

        for v in r.values():
            response = await self.get_mongo_client().get_all_files_trashed(int(v))
            if response['status'] == 'success':
                all_data.extend(response['data'])
            else:
                return error("Error getting trashed files")

        return success("Get all trashed files", all_data)

    # Get all folders by cluster_id
    async def get_all_folders_by_cluster_id(self, cluster_id):
        return await self.get_mongo_client().get_all_folders_by_cluster_id(cluster_id)

    # --------------------------------------------------------------------
    # --------------------------------------------------------------------
    # --------------------------------------------------------------------

    # Rename file -- OK
    async def rename_file(self, cluster_id, file_id, new_name):
        return await self.mongo.update_file_name(cluster_id, file_id, new_name)

    # Move file -- OK
    async def move_file(self, cluster_id, file_id, new_location):
        return await self.mongo.update_file_location(cluster_id, file_id, new_location)

    # Delete file -- OK
    async def delete_file(self, cluster_id, file_id):

        file = await self.mongo.get_file_by_id(cluster_id, file_id)

        if file["status"] != "success":
            return file
        else:
            if file["data"]["locate_media"] == "./trash":
                # Delete
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
            else:
                return await self.mongo.trash_file(cluster_id, file_id)

    # Upload file -- OK
    async def upload_file(self, file, scr_destination, cluster_id, file_size):
        try:
            r1 = await self.client.upload_file(file, scr_destination, cluster_id, file_size)
            if r1['status'] == 'error':
                return {'status': 'error', 'message': r1["message"]}
            else:
                await self.sync_drive()
                return r1
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    async def download_file(self, cluster_id, file_id):
        try:
            async_gen = await self.client.download_file(file_id, cluster_id)
            return async_gen
        except Exception as e:
            raise e

    # Create folder -- OK
    async def create_folder(self, cluster_id, folder_path):
        return await self.get_mongo_client().create_folder(cluster_id, folder_path)

    # Create folder -- OK
    async def delete_folder(self, cluster_id, folder_path):
        # Get all file in folder
        r = await self.get_mongo_client().get_files_in_folder_including_subfolders(cluster_id, folder_path)
        if len(r["data"]) != 0:
            return error("Unable to delete folder that contains files")

        r = await self.get_mongo_client().has_subfolders(cluster_id, folder_path)
        if r["data"]:
            return error("Unable to delete folder that contains subfolders")

        return await self.get_mongo_client().delete_folder(cluster_id, folder_path)

    # Rename folder
    async def rename_folder(self, cluster_id, old_path_folder, new_name):
        return await self.get_mongo_client().rename_folder(cluster_id, old_path_folder, new_name)


async def main():
    # Init layer4
    l = Layer4()
    await l.initialize()



if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
