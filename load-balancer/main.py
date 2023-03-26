from flask import Flask, Response, jsonify, request
import urllib.parse
import requests
import itertools
import os
import logging

app = Flask(__name__)

# Bypass for logging messages to Guinocorn
if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)


BASE_URL = "https://storage.googleapis.com/"

# List of backend servers
BACKEND_SERVERS = [
    "decentrilized-cdn-eu-central-2",
    "decentrilized-cdn-eu-west-1"
]

# Initialize the round-robin iterator
RR = itertools.cycle(BACKEND_SERVERS)

@app.before_request
def block_http_methods():
    if request.method != 'GET':
        return jsonify({'error': 'HTTP method not allowed'}), 405

@app.errorhandler(404)
def page_not_found(error):
    return jsonify({'Error': 'Page not found'}), 404
    
@app.route('/<key>', methods=['GET'])
def download(key):
    # Go to the next backend
    backend_url = next(RR)

    # Logs backend being used and URL Path
    app.logger.info("Using '%s' to process GET /%s", backend_url, key)

    # Construct the full backend URL including the path
    full_backend_url = urllib.parse.urljoin(BASE_URL,  backend_url + "/" + key)

    # Download the file using requests.get()
    response = requests.get(full_backend_url, stream=True)
    
    # Check if the response was successful
    if response.status_code != 200:
        return jsonify({'Error': 'Failed to download file'}), 404

    # Set the content type and disposition headers
    headers = {
        'Content-Type': response.headers.get('Content-Type'),
        'Content-Disposition': 'attachment; filename={}'.format(response.headers.get('Content-Disposition'))
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
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))