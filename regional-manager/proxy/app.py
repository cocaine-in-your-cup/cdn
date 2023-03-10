import http.server
import socketserver
import urllib.parse
import requests
import itertools
import uuid
import threading
import logging

# Create a custom formatter that removes the "root" logger prefix
class CustomFormatter(logging.Formatter):
    def format(self, record):
        record = logging.makeLogRecord(record.__dict__)
        return super().format(record)

# Set up logging with a custom formatter and handler
formatter = CustomFormatter("%(asctime)s %(levelname)s %(message)s")
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logging.basicConfig(level=logging.INFO, handlers=[handler])

BASE_URL = "https://storage.googleapis.com/"

# List of backend servers
BACKEND_SERVERS = [
    "decentrilized-cdn-eu-central-2",
    "decentrilized-cdn-eu-west-1"
]

# Initialize the round-robin iterator
RR = itertools.cycle(BACKEND_SERVERS)

class ProxyHandler(http.server.BaseHTTPRequestHandler):

    # Initialize the backend_url variable with the first server from the BACKEND_SERVERS list
    backend_url = next(RR)
    
    def do_GET(self):
        # Get the URL path from the client request
        url_path = self.path

        # If URL path is favicon request block it
        if self.path == "/favicon.ico":
            self.send_error(404)
            return

        # If a backend server was selected for a non-root path, store it as the last selected backend server
        if self.path != "/":
            last_backend_url = self.backend_url

        # If URL path is root, use the current backend server
        if self.path == "/":
            backend_url = self.backend_url
        else:
            # Select the next backend server in round-robin fashion
            backend_url = next(RR)

        # Construct the full backend URL including the path
        full_backend_url = urllib.parse.urljoin(BASE_URL,  backend_url + url_path)

        # Set header to request to google bucket, needs x-goog-project-id for authentication
        headers = {'x-goog-project-id': backend_url}

        # Forward the client request to the backend server
        response = requests.get(full_backend_url, headers=headers, stream=True)

        # Send the backend server response headers to the client
        self.send_response(response.status_code)
        self.send_header("Content-type", response.headers.get('Content-Type'))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        
        # Stream the response content to the client in chunks
        for i, chunk in enumerate(response.iter_content(chunk_size=4096), 1):
            if chunk:
                logging.info("---- [ Chunk %d ] %s ", i, chunk)
                self.wfile.write(chunk)

        logging.info("Incoming request:")
        logging.info("Method: %s", self.command)
        logging.info("Path: %s", self.path)
        logging.info("Protocol version: %s", self.request_version)
        logging.info("Headers:\n%s", self.headers)
    
    # Prevent all other methods
    def do_POST(self):
        self.send_error(405, "Method Not Allowed")
        
    def do_PUT(self):
        self.send_error(405, "Method Not Allowed")
        
    def do_PATCH(self):
        self.send_error(405, "Method Not Allowed")
        
    def do_DELETE(self):
        self.send_error(405, "Method Not Allowed")
        
    def do_OPTIONS(self):
        self.send_error(405, "Method Not Allowed")
        
    def do_HEAD(self):
        self.send_error(405, "Method Not Allowed")

class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

if __name__ == "__main__":
    # Start the HTTP server on port 8000
    with ThreadedHTTPServer(("", 8000), ProxyHandler) as httpd:
        logging.info("HTTP server listening on port 8000...")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logging.info("KeyboardInterrupt received, shutting down server...")
            httpd.shutdown()
