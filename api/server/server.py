import json

from quart import Quart, request, jsonify, g
from api.mongodb.mongodb_login import MongoDBLogin
from api.telegram.layer_4 import Layer4
from utils.config import config
from functools import wraps
import asyncio

app = Quart(__name__)

layer4 = Layer4()


async def initialize():
    await layer4.initialize()


@app.before_serving
async def setup():
    await initialize()


def get_mongo_connection():
    if 'mongo' not in g:
        g.mongo = MongoDBLogin(config.SECRET_KEY)
    return g.mongo


def token_required(f):
    @wraps(f)
    async def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        auth = get_mongo_connection()
        if not token:
            return jsonify({'status': 'error', 'message': 'Token not provided in headers'}), 400
        if not auth.verify_token(token):
            return jsonify({'status': 'error', 'message': 'Invalid or expired token'}), 401

        g.token = token

        return await f(*args, **kwargs)

    return decorated


# Login -- return auth token -- OK
@app.route('/login', methods=['POST'])
async def login():
    data = await request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'status': 'error', 'message': 'Invalid parameters'}), 400

    auth = get_mongo_connection()
    token = auth.login(email, password)
    if token:

        # Fetch id cluster
        ds_id = auth.get_user_by_token(token)
        print(ds_id)
        if not ds_id:
            return jsonify({'status': 'error', 'message': "Internal Error -- can't retrieve ds_id"}), 401

        #clusters_info = await layer4.get_clusters_info()
        #print(clusters_info)

        return jsonify({'status': 'success', 'token': token}), 200
    else:
        return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401


# Verify token -- verify auth token -- OK
@app.route('/verify-token', methods=['GET'])
@token_required
async def verify_token():
    return jsonify({'status': 'success', 'message': 'Valid token'}), 200


# Logout
@app.route('/logout', methods=['POST'])
@token_required
async def logout():
    token = request.headers.get('Authorization')
    auth = get_mongo_connection()

    if auth.logout(token):
        return jsonify({'status': 'success', 'message': 'Logout successful'}), 200
    else:
        return jsonify({'status': 'error', 'message': 'Error during logout'}), 400


# Layer4 - Sync Drive -- Sync drive-telegram -- OK
@app.route('/sync-drive', methods=['POST'])
@token_required
async def sync_drive():
    result = await layer4.sync_drive()
    return jsonify(result)


# Layer4 - Get Clusters Info -- OK
@app.route('/clusters', methods=['POST'])
@token_required
async def get_clusters_info():
    result = await layer4.get_clusters_info()
    return jsonify(result)


# Layer4 - Get All Files in Cluster
@app.route('/get-all-files', methods=['POST'])
@token_required
async def get_all_files():
    result = await layer4.get_all_file(g.id_private_cluster)
    return jsonify(result)


# Layer4 - Get File Info
@app.route('/get-file-info', methods=['POST'])
@token_required
async def get_file_info():
    data = await request.json
    file_id = data.get('file_id')

    if not file_id:
        return jsonify({'status': 'error', 'message': 'Cluster ID and File ID are required'}), 400

    result = await layer4.get_file_info(g.id_private_cluster, file_id)
    return jsonify(result)


# Layer4 - Rename File
@app.route('/rename-file', methods=['POST'])
@token_required
async def rename_file():
    data = await request.json
    cluster_id = data.get('cluster_id')
    file_id = data.get('file_id')
    new_name = data.get('new_name')

    if not cluster_id or not file_id or not new_name:
        return jsonify({'status': 'error', 'message': 'Cluster ID, File ID, and New Name are required'}), 400

    result = await layer4.rename_file(cluster_id, file_id, new_name)
    return jsonify(result)


# Layer4 - Move File
@app.route('/move-file', methods=['POST'])
@token_required
async def move_file():
    data = await request.json
    cluster_id = data.get('cluster_id')
    file_id = data.get('file_id')
    new_location = data.get('new_location')

    if not cluster_id or not file_id or not new_location:
        return jsonify({'status': 'error', 'message': 'Cluster ID, File ID, and New Location are required'}), 400

    result = await layer4.move_file(cluster_id, file_id, new_location)
    return jsonify(result)


# Layer4 - Move to Trash
@app.route('/move-to-trash', methods=['POST'])
@token_required
async def move_to_trash():
    data = await request.json
    cluster_id = data.get('cluster_id')
    file_id = data.get('file_id')

    if not cluster_id or not file_id:
        return jsonify({'status': 'error', 'message': 'Cluster ID and File ID are required'}), 400

    result = await layer4.move_to_trash(cluster_id, file_id)
    return jsonify(result)


# Layer4 - Delete File
@app.route('/delete-file', methods=['DELETE'])
@token_required
async def delete_file():
    data = await request.json
    cluster_id = data.get('cluster_id')
    file_id = data.get('file_id')

    if not cluster_id or not file_id:
        return jsonify({'status': 'error', 'message': 'Cluster ID and File ID are required'}), 400

    result = await layer4.delete_file(cluster_id, file_id)
    return jsonify(result)


# Layer4 - Upload File
@app.route('/upload', methods=['POST'])
@token_required
async def upload_file():
    src_file = await request.files.get('file')
    scr_destination = await request.form.get('destination')
    cluster_id = await request.form.get('cluster_id')

    if not src_file or not scr_destination or not cluster_id:
        return jsonify({'status': 'error', 'message': 'File, Destination, and Cluster ID are required'}), 400

    result = await layer4.upload_file(src_file, scr_destination, cluster_id)
    return jsonify(result)


# Layer4 - Download File
@app.route('/download', methods=['POST'])
@token_required
async def download_file():
    data = await request.json
    cluster_id = data.get('cluster_id')
    file_id = data.get('file_id')
    dest = data.get('dest')
    name_file = data.get('name_file')

    if not cluster_id or not file_id or not dest or not name_file:
        return jsonify(
            {'status': 'error', 'message': 'Cluster ID, File ID, Destination, and File Name are required'}), 400

    result = await layer4.download_file(cluster_id, file_id, dest, name_file)
    return jsonify(result)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
