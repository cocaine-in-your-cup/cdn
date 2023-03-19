from http import HTTPStatus
from flask import Flask, request, abort
from werkzeug.utils import secure_filename
import requests
import os
from utils import list_regional_managers_ips
from dotenv import load_dotenv
load_dotenv()

"""
API responsible for the propagation of file PUT/DELETE events to the Regional Managers.
Works as the Admin Client's endpoint for PUT/DELETE events.
"""

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "I'm up and running!"


@app.route("/files", methods=['POST'])
def uploadFile():
    """
    Propagate file upload to all the Regional Managers
    Warning: Accepts self-signed SSL certificates
    Warning: No Oauth2.0 added
    Warning: Single Threaded making it quite slow and not scalable
    Warning: If an error occurs at occurs at any of the Regional Managers API the program will ignore it and return successful (200).
    """
    # check if the post request has the file part
    if 'file' not in request.files:
        abort(HTTPStatus.NOT_FOUND, description="No file part found")
    file = request.files['file']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        abort(HTTPStatus.NOT_FOUND, description="No file selected")
    if file and file.filename:
        file_name = secure_filename(file.filename)
        # for ip in list_regional_managers_ips(projectID).values():
        #     url = f"https://{ip}:{region_managers_port}"
        for ip in {"region manager" : "127.0.0.1" }.values():
            url = f"https://{ip}:{region_managers_port}/files"
            # print("stream ", file.stream.read())  
            region_manager_ssl_key = f'{cert_folder}key_region_manager.pem'
            r = requests.post(f'{url}', files={'file': (file_name, file.stream, file.mimetype)}, verify=False)
            print(r.text)
        return f"<p>Uploaded {file_name}!</p>"
    abort(HTTPStatus.INTERNAL_SERVER_ERROR, description="")


host = os.environ.get('FLASK_SERVER_HOST')
port = os.environ.get('FLASK_SERVER_PORT')
cert_folder = os.environ.get('CERT_FOLDER')
projectID = os.environ.get('GCP_PROJECT_ID')
region_managers_port = os.environ.get('REGIONAL_MANAGERS_API_PORT')


if __name__ == '__main__':
    # Launch the application
    app.run(ssl_context=(f'{cert_folder}/cert.pem', f'{cert_folder}/key.pem'), host=host, port=port)
    # app.run(host=host, port=port)
