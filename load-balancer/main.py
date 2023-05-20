from flask import Flask, Response, jsonify, request
import urllib.parse
import requests
import itertools
import os
import logging
import xml.etree.ElementTree as ET
from pythonp2p import Node

app = Flask(__name__)

# Bypass for logging messages to Guinocorn
if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)


# P2P configuration
HOST = '0.0.0.0'
PORT = 65432
FILE_PORT = 65433

# Initialize the P2P node
p2p_node = Node(HOST, PORT, FILE_PORT)


BASE_URL = "https://storage.googleapis.com/"

# List of backend servers
BACKEND_SERVERS = os.environ.get('BACKEND_SERVERS', '').split(',')

if not BACKEND_SERVERS:
    raise ValueError('BACKEND_SERVERS environment variable is not set')
    
# Initialize the round-robin iterator
RR = itertools.cycle(BACKEND_SERVERS)
backend_url = ""

@app.route('/', methods=['GET'])
def index():
    # Go to the next backend
    backend_url = next(RR)
    full_backend_url = urllib.parse.urljoin(BASE_URL,  backend_url + "/")

    response = requests.get(full_backend_url)

    xml_string = response.content.decode('utf-8')
    root = ET.fromstring(xml_string)
    
    # Gets name of bucket
    name = root.findtext('{http://doc.s3.amazonaws.com/2006-03-01}Name')
    # Get the table data
    items = []
    for elem in root.iter('{http://doc.s3.amazonaws.com/2006-03-01}Contents'):
        items.append({'key': elem.findtext('{http://doc.s3.amazonaws.com/2006-03-01}Key'),
                      'generation': elem.findtext('{http://doc.s3.amazonaws.com/2006-03-01}Generation'),
                      'meta_generation': elem.findtext('{http://doc.s3.amazonaws.com/2006-03-01}MetaGeneration'),
                      'last_modified': elem.findtext('{http://doc.s3.amazonaws.com/2006-03-01}LastModified'),
                      'etag': elem.findtext('{http://doc.s3.amazonaws.com/2006-03-01}ETag'),
                      'size': elem.findtext('{http://doc.s3.amazonaws.com/2006-03-01}Size')})
    return items
@app.route('/<key>', methods=['GET'])
def download(key=None):
    # Go to the next backend
    backend_url = next(RR)

    if key:
        # Logs backend being used and URL Path
        app.logger.info("Using '%s' to process GET /%s", backend_url, key)

        # Construct the full backend URL including the path
        full_backend_url = urllib.parse.urljoin(BASE_URL,  backend_url + "/" + key)
    else:
        # Logs backend being used and URL Path
        app.logger.info("Using '%s' to process GET /", backend_url)

        # Construct the full backend URL including the path
        full_backend_url = urllib.parse.urljoin(BASE_URL,  backend_url + "/")

    # Download the file using requests.get()
    response = requests.get(full_backend_url, stream=True)
    
    # Check if the response was successful
    if response.status_code != 200:
        return jsonify({'Error': 'Failed to download file'}), 404

    # Set the content type and disposition headers
    headers = {
        'Content-Type': response.headers.get('Content-Type'),
        'Content-Disposition': 'attachment; filename={}'.format(response.headers.get('Content-Disposition')),
        'Content-Length': response.headers.get('Content-Length')
    }

    # Create a generator function to yield the file data in chunks
    def generate():
        for chunk in response.iter_content(int(os.environ.get("CHUNK_SIZE", 4096))):
            if chunk:
                # app.logger.info('Received a chunk of size %d - %s', len(chunk), chunk)
                yield chunk

    # Return a Flask response object with the generator function
    return Response(generate(), headers=headers, status=200)

if __name__ == '__main__':
    p2p_node.start()
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))