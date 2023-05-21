"""
API responsible for propagating data changes to all the buckets under its region.
"""

import asyncio
from http import HTTPStatus
from flask import Flask, Response, request, abort
from werkzeug.utils import secure_filename
import os
from google.cloud import storage
import base64
from functools import wraps

from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.storage import Storage

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import Session
else:
    from aiohttp import ClientSession as Session

storage_client = storage.Client() # Used only to list buckets

# Retrieve environment variables with error checking
region = os.environ.get('REGION')
if not region:
    raise ValueError("REGION environment variable is not set")

user = os.environ.get('USER')
if not user:
    raise ValueError("USER environment variable is not set")

password = os.environ.get('PASSWORD')
if not password:
    raise ValueError("USER environment variable is not set")

app = Flask(__name__)
    
@app.route("/")
def hello_world():
    return "I'm up and running!"

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization')
        if auth:
            username, password = base64.b64decode(auth.split(' ')[1]).decode().split(':')
            # Validate the username and password
            if username == user and password == password:
                return f(*args, **kwargs)

        # If authentication fails, return a 401 Unauthorized status
        return abort(HTTPStatus.UNAUTHORIZED, description="Unauthorized")

    return decorated

@app.route("/files", methods=['POST'])
@requires_auth
async def uploadFile():
    """
    Propagate a file upload to all the buckets under its region.
    Warning: No Oauth2.0 added
    """
    # check if the post request has the file part
    if 'file' not in request.files:
        abort(HTTPStatus.NOT_FOUND, description="No file part found")
    file = request.files['file']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        abort(HTTPStatus.NOT_FOUND, description="No file selected")
    if file and file.filename: # If we have a name and content then upload the file
        file_name = secure_filename(file.filename)
        file_contents=file.stream.read()
        # Upload to all buckets under its region
        async with Session() as session:
            aio_storage_client = Storage(session=session) 
            tasks = [aio_storage_client.upload(bucket_id, file_name, file_contents) for bucket_id in listBuckets(storage_client, region.lower())]
            await asyncio.gather(*tasks, return_exceptions=True)
        return Response(f"<p>Uploaded {file_name} for all buckets in the {region} region!</p>", status=200, mimetype='text/plain')
    abort(HTTPStatus.INTERNAL_SERVER_ERROR, description="Something went wrong")


def listBuckets(client: storage.Client, region_acronym: str) -> list[str]:
    """
    List the buckets that belong to a certain region.
    """
    region_buckets = []
    for bucket in client.list_buckets():
        if f"decentrilized-cdn-{region_acronym}" in bucket.name:
            region_buckets.append(bucket.name)
    return region_buckets


if __name__ == '__main__':
    # Launch the application
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

