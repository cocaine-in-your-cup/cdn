import os
import aiohttp
import asyncio
import signal
import logging
import base64
from aiohttp import web
from werkzeug.utils import secure_filename
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.storage import Storage
from google.cloud import storage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Retrieve USER_DB from environment variables
user_db_env = os.environ.get('USER_DB')
USER_DB = eval(user_db_env) if user_db_env else {}

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


# Authentication function
async def authenticate(request):
    # Get username and password from the request
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Basic '):
        auth_token = auth_header[6:]
        auth_token_bytes = base64.b64decode(auth_token).decode('utf-8')
        username, password = auth_token_bytes.split(':')

        # Check if the username and password are valid
        if username in USER_DB and USER_DB[username] == password:
            return True
    
    return False

# Protected route handler
async def protected_handler(request):
    authenticated = await authenticate(request)
    if authenticated:
        logger.info('Access granted to protected route')
        return web.Response(text='This is a protected route')
    else:
        logger.warning('Access denied to protected route')
        return web.Response(status=401, text='Unauthorized')

# Public route handler
async def public_handler(request):
    logger.info('Accessed public route')
    return web.Response(text='This is a public route')

# Redirect handler
async def redirect_handler(request):
    raise web.HTTPFound(location='/')

# Signal handler for server shutdown
async def shutdown(signal, loop):
    logger.info('Server shutting down...')
    tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

def listBuckets(client: storage.Client, region_acronym: str) -> list[str]:
    """
    List the buckets that belong to a certain region.
    """
    region_buckets = []
    for bucket in client.list_buckets():
        if f"decentrilized-cdn-{region_acronym}" in bucket.name:
            region_buckets.append(bucket.name)
    return region_buckets

# Upload file handler
async def upload_file_handler(request):
    """
    Propagate a file upload to all the buckets under its region.
    Warning: No Oauth2.0 added
    """
    authenticated = await authenticate(request)
    if not authenticated:
        logger.warning('Access denied to file upload')
        return web.Response(status=401, text='Unauthorized')
    # Check if the request contains multipart data
    if not request.content_type.startswith('multipart/'):
        logger.warning('Invalid request. Expected multipart/form-data.')
        return web.Response(status=400, text='Invalid request. Expected multipart/form-data.')

    # Process the multipart data
    reader = await request.multipart()
    
    # Find the file part
    file_field = await reader.next()
    if file_field.name != 'file':
        logger.warning('Invalid request. Missing file field.')
        return web.Response(status=400, text='Invalid request. Missing file field.')

    # Get the file name and contents
    file_name = secure_filename(file_field.filename)
    file_contents = await file_field.read()

    # Upload to all buckets under its region
    storage_client = storage.Client()
    bucket_ids = listBuckets(storage_client, region.lower())  # Replace with appropriate logic to get bucket IDs
    for bucket_id in bucket_ids:
        bucket = storage_client.get_bucket(bucket_id)
        blob = bucket.blob(file_name)
        blob.upload_from_string(bytes(file_contents))
    
    logger.info(f'File "{file_name}" uploaded successfully for all buckets in the {region} region.')
    return web.Response(text=f"<p>Uploaded {file_name} for all buckets in the {region} region!</p>", status=200, content_type='text/plain')

# Main server function
async def main():
    app = web.Application()
    
    # Register the route handlers
    app.router.add_get('/protected', protected_handler)
    app.router.add_get('/', public_handler)
    app.router.add_get('/{tail:.*}', redirect_handler)  # Capture all paths and redirect
    app.router.add_post('/files', upload_file_handler)

    # Start the server
    runner = web.AppRunner(app)
    await runner.setup()
    # site = web.TCPSite(runner, 'localhost', 8080)
    site = web.TCPSite(runner, '0.0.0.0', port=int(os.environ.get("PORT", 8080)))  # Listen on all available network interfaces
    await site.start()
    logger.info('Server started at http://localhost:8080')
    
    # Register the signal handler for graceful shutdown
    loop = asyncio.get_running_loop()
    signals = (signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(s, lambda s=s: asyncio.create_task(shutdown(s, loop)))
    
    # Wait for the server to be closed
    await asyncio.Event().wait()

# Run the server
if __name__ == '__main__':
    asyncio.run(main())
