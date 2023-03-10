import http.server
import socketserver
import urllib.parse
import requests
import itertools

BASE_URL = "https://storage.googleapis.com/"
# List of backend servers
BACKEND_SERVERS = [
    "decentrilized-cdn-na-east-1",
    "decentrilized-cdn-eu-west-1"
]

# Initialize the round-robin iterator
RR = itertools.cycle(BACKEND_SERVERS)

class ProxyHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        # Get the URL path from the client request
        url_path = self.path

        # If URL path is favicon request block it
        if self.path == "/favicon.ico":
            self.send_error(404)
            return

        # Get the next backend server URL from the round-robin iterator
        backend_url = next(RR)

        # Construct the full backend URL including the path
        full_backend_url = urllib.parse.urljoin(BASE_URL, backend_url + url_path)

        
        # Set header to request to google bucket, needs x-goog-project-id for authentication
        headers = {
            'x-goog-project-id': backend_url,
            'Content-type': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
        }

        # Forward the client request to the backend server
        response = requests.get(full_backend_url, headers=headers, stream=True)
        response_content_type = response.headers.get('Content-Type')

        # Send the backend server response headers to the client
        self.send_response(response.status_code)
        self.send_header("Content-type", response_content_type)
        self.end_headers()

        # Stream the response content to the client in chunks
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                print("chunk = ", chunk)
                self.wfile.write(chunk)

        print("Incoming request:")
        print(f"Method: {self.command}")
        print(f"Path: {self.path}")
        print(f"Protocol version: {self.request_version}")
        print(f"Headers:\n{self.headers}")

if __name__ == "__main__":
    # Start the HTTP server on port 8000
    with socketserver.TCPServer(("", 8000), ProxyHandler) as httpd:
        print("HTTP server listening on port 8000...")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt received, shutting down server...")
            httpd.shutdown()
