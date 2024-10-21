import asyncio

from quart import Quart, session, request, jsonify, g, Response
from api.mongodb.mongodb_login import MongoDBLogin
from api.telegram.layer_4 import Layer4
from utils.config import config
from functools import wraps
from utils.utils_functions import get_value_from_string
from quart_cors import cors

app = Quart(__name__)
app.secret_key = config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB


app = cors(app, allow_origin="*")

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
        usr = auth.get_user_by_token(token)
        if not usr:
            return jsonify({'status': 'error', 'message': "Internal Error -- can't retrieve usr"}), 401

        clusters_info = await layer4.get_clusters_info()
        cluster_id_prv = get_value_from_string(clusters_info, usr["discord_id"])
        cluster_id_pub = get_value_from_string(clusters_info, "Drive_Layer_Shared")
        if not cluster_id_prv or not cluster_id_pub:
            return jsonify({'status': 'error', 'message': "Internal Error -- can't retrieve cluster's id"}), 401

        print(usr)
        return jsonify({'status': 'success', 'token': token, 'r': cluster_id_pub, 'u': cluster_id_prv,
                        'lastLogin': usr["last_login"], "role": usr["role"], "urlAvatar": usr["url_avatar"]}), 200
    else:
        return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401


# Verify token -- verify auth token -- OK
@app.route('/verify-token', methods=['GET'])
@token_required
async def verify_token():
    return jsonify({'status': 'success', 'message': 'Valid token'}), 200


@app.route('/ping-pong', methods=['GET'])
async def ping():
    #print(layer4.is_connect())
    return jsonify({'status': 'success', 'message': layer4.is_connect()})


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
@app.route('/sync-drive', methods=['GET'])
@token_required
async def sync_drive():
    return jsonify(await layer4.sync_drive())


# Layer4 - Get All Files in private cluster -- OK
@app.route('/get-all-files', methods=['POST'])
@token_required
async def get_all_files():
    data = await request.json
    cluster_id_private = data.get('cluster_id')

    if not cluster_id_private:
        return jsonify({'status': 'error', 'message': "Internal Error -- cluster_id_private not found"}), 500

    return jsonify(await layer4.get_all_file(int(cluster_id_private)))


# Layer4 - Get All Files in public cluster -- OK
@app.route('/get-all-files-public', methods=['POST'])
@token_required
async def get_all_files_public():
    data = await request.json
    cluster_id_public = data.get('cluster_id')
    if not cluster_id_public:
        return jsonify({'status': 'error', 'message': "Internal Error -- cluster_id_public not found"}), 500

    return jsonify(await layer4.get_all_file(int(cluster_id_public)))


# Layer4 - Get trashed files -- OK
@app.route('/get-trash-files', methods=['GET'])
@token_required
async def get_trash_files():
    return jsonify(await layer4.get_file_trashed())


# Layer4 - Get File Info -- OK
@app.route('/get-file-info', methods=['GET'])
@token_required
async def get_file_info():
    data = await request.json
    file_id = data.get('file_id')
    id_cluster = data.get('c')

    if not file_id or not id_cluster:
        return jsonify({'status': 'error', 'message': 'C and File ID are required'}), 400
    else:
        result = await layer4.get_file_info(int(id_cluster), file_id)
        return jsonify(result)


# Layer4 - Rename File -- OK
@app.route('/rename-file', methods=['POST'])
@token_required
async def rename_file():
    data = await request.json
    id_cluster = data.get('c')
    file_id = data.get('file_id')
    new_name = data.get('new_name')

    if not id_cluster or not file_id or not new_name:
        return jsonify({'status': 'error', 'message': 'c, File ID, and New Name are required'}), 400
    else:
        result = await layer4.rename_file(id_cluster, file_id, new_name)
        return jsonify(result)


# Layer4 - Move File -- OK
@app.route('/move-file', methods=['POST'])
@token_required
async def move_file():
    data = await request.json
    id_cluster = data.get('c')
    file_id = data.get('file_id')
    new_location = data.get('new_location')

    if not id_cluster or not file_id or not new_location:
        return jsonify({'status': 'error', 'message': 'C, File ID, and New Location are required'}), 400
    else:
        result = await layer4.move_file(id_cluster, file_id, new_location)
        return jsonify(result)


# Layer4 - Get all folder by cluster_id -- OK
@app.route('/get-folders', methods=['POST'])
@token_required
async def get_folders():
    data = await request.json
    id_cluster = data.get('c')

    if not id_cluster:
        return jsonify({'status': 'error', 'message': 'C is required'}), 400
    else:
        result = await layer4.get_all_folders_by_cluster_id(id_cluster)
        return jsonify(result)


# Layer4 - Get all folder by cluster_id -- OK
@app.route('/get-clusters-info', methods=['GET'])
@token_required
async def get_clusters_info():
    return jsonify({'status': 'success', 'message': 'Successfully', 'data': await layer4.get_clusters_info()})


# Layer4 - Delete File -- OK
@app.route('/delete-file', methods=['POST'])
@token_required
async def delete_file():
    data = await request.json
    id_cluster = data.get('c')
    file_id = data.get('file_id')

    if not id_cluster or not file_id:
        return jsonify({'status': 'error', 'message': 'C and File ID are required'}), 400
    else:
        result = await layer4.delete_file(id_cluster, file_id)
        return jsonify(result)


# Layer4 - Upload File
@app.route('/upload', methods=['POST'])
@token_required
async def upload_file():
    form = await request.form
    files = await request.files

    if 'file' not in files:
        return jsonify({'status': 'error', 'message': 'Il file è richiesto'}), 400

    file = files['file']
    scr_destination = form.get('destination')
    id_cluster = form.get('c')
    file_size = form.get('file_size')

    if not file or not scr_destination or not id_cluster or not file_size:
        return jsonify({'status': 'error', 'message': 'File, Destination, id_cluster e file_size sono richiesti'}), 400

    try:
        file_size = int(file_size)
    except ValueError:
        return jsonify({'status': 'error', 'message': 'file_size deve essere un intero'}), 400

    result = await layer4.upload_file(file, scr_destination, id_cluster, file_size)
    return jsonify(result)


@app.route('/download', methods=['POST'])
@token_required
async def download_file():
    data = await request.json
    cluster_id = data.get('cluster_id')
    file_id = data.get('file_id')
    name_file = data.get('name_file')

    if not cluster_id or not file_id or not name_file:
        return jsonify(
            {'status': 'error', 'message': 'Cluster ID, File ID, and File Name are required'}), 400

    try:
        async_gen = await layer4.download_file(cluster_id, file_id)

        async def generate():
            try:
                async for chunk in async_gen:
                    yield chunk
            except Exception as e:
                print(f"Errore durante il download: {e}")

        headers = {
            'Content-Disposition': f'attachment; filename="{name_file}"'
        }
        return Response(generate(), headers=headers, content_type='application/octet-stream')
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# Layer4 - Create Folder
@app.route('/create-folder', methods=['POST'])
@token_required
async def create_folder():
    data = await request.json
    cluster_id = data.get('c')
    folder_path = data.get('folder_path')

    if not cluster_id or not folder_path:
        return jsonify(
            {'status': 'error', 'message': 'Cluster ID, Folder Path are required'}), 400

    result = await layer4.create_folder(cluster_id, folder_path)
    return jsonify(result)


# Layer4 - Delete Folder without any file inside
@app.route('/delete-folder', methods=['POST'])
@token_required
async def delete_folder():
    data = await request.json
    cluster_id = data.get('c')
    folder_path = data.get('folder_path')

    if not cluster_id or not folder_path:
        return jsonify(
            {'status': 'error', 'message': 'Cluster ID, Folder Path are required'}), 400

    result = await layer4.delete_folder(cluster_id, folder_path)
    return jsonify(result)


# Layer4 - Rename folder
@app.route('/rename-folder', methods=['POST'])
@token_required
async def rename_folder():
    data = await request.json
    cluster_id = data.get('c')
    old_path_folder = data.get('old_path_folder')
    new_name = data.get('new_name')

    if not cluster_id or not old_path_folder or not new_name:
        return jsonify(
            {'status': 'error', 'message': 'Cluster ID, Folder Paths are required'}), 400

    result = await layer4.rename_folder(cluster_id, old_path_folder, new_name)
    return jsonify(result)


if __name__ == '__main__':
    app.run(host='192.168.1.11', port=5000)
