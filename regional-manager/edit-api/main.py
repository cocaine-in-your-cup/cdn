"""
API responsible for propagating data changes to all the buckets under its region.
"""

import asyncio
from http import HTTPStatus
from flask import Flask, request, abort
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
from google.cloud import storage

from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.storage import Storage
# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import Session
else:
    from aiohttp import ClientSession as Session

load_dotenv()
storage_client = storage.Client() # Used only to list buckets
region: str = os.environ.get('REGION', "Environment variable does not exist")

app = Flask(__name__)
    
@app.route("/")
def hello_world():
    return "I'm up and running!"


@app.route("/files", methods=['POST'])
async def uploadFile():
    """
    Propagate a file upload to all the buckets under its region.
    Warning: Accepts self-signed SSL certificates
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
        return f"<p>Uploaded {file_name} for all buckets in the {region} region!</p>"
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

host = os.environ.get('FLASK_SERVER_HOST')
port = os.environ.get('FLASK_SERVER_PORT')
cert_path = os.environ.get('CERT_FOLDER')

if __name__ == '__main__':
    # Launch the application
    app.run(ssl_context=(f'{cert_path}/cert.pem', f'{cert_path}/key.pem'), host=host, port=port)

