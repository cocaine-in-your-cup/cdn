"""
API responsible for propagating data changes to all the buckets under its region.
"""

from http import HTTPStatus
import io
from typing import IO
from flask import Flask, request, abort
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
from google.cloud import storage

load_dotenv()
storage_client = storage.Client()
region: str = os.environ.get('REGION', "Environment variable does not exist")

app = Flask(__name__)


@app.route("/")
def hello_world():
    return "I'm up and running!"


@app.route("/files", methods=['POST'])
def uploadFile():
    # check if the post request has the file part
    if 'file' not in request.files:
        abort(HTTPStatus.NOT_FOUND, description="No file part found")
    file = request.files['file']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        abort(HTTPStatus.NOT_FOUND, description="No file selected")
    if file and file.filename:
        file_content = file.stream
        file_name = secure_filename(file.filename)
        # Upload to all buckets under its region
        for bucket_id in listBuckets(storage_client, region.lower()):
            uploadToBucket(bucket_id, file_name, file_content)
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


def uploadToBucket(bucket_id: str, file_name: str, file_content: IO[bytes]):
    """
    Upload a stream to a specific bucket
    """
    bucket = storage_client.bucket(bucket_id)
    blob = bucket.blob(file_name)
    blob.upload_from_file(file_content)
    file_content.seek(0)
    # print("Stored", file_name, "with content",
    #       file_content, "in", bucket_id)


host = os.environ.get('FLASK_SERVER_HOST',
                      "Environment variable does not exist")
port = os.environ.get('FLASK_SERVER_PORT',
                      "Environment variable does not exist")
cert_path = os.environ.get('CERT_FOLDER',
                      "Environment variable does not exist")

if __name__ == '__main__':
    # Launch the application
    app.run(ssl_context=(f'{cert_path}/cert.pem', f'{cert_path}/key.pem'), host=host, port=port)
