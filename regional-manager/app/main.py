from flask import Flask, render_template, send_file, Response
from flask_table import Table, Col, LinkCol
import requests
import xml.etree.ElementTree as ET
import os

app = Flask(__name__)

ip = os.environ.get('REGION_PROXY')
if not ip:
    raise ValueError('REGION_PROXY environment variable is not set')
    
url = 'http://' + ip + '/'

# Define the table structure
class ItemTable(Table):
    key = Col('Key')
    generation = Col('Generation')
    meta_generation = Col('MetaGeneration')
    last_modified = Col('LastModified')
    etag = Col('ETag')
    size = Col('Size')
    download_ref = LinkCol('Download', 'download', url_kwargs=dict(key='key'))

@app.route('/<key>', methods=['GET'])
def download(key):
    # Download the file using requests.get()
    response = requests.get(url + key, stream=True)
    
    # Check if the response was successful
    if response.status_code != 200:
        return "Error: Failed to download file"

    # Set the content type and disposition headers
    headers = {
        'Content-Type': response.headers.get('Content-Type'),
        'Content-Disposition': 'attachment; filename={}'.format(response.headers.get('Content-Disposition'))
    }

    # Create a generator function to yield the file data in chunks
    def generate():
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                yield chunk

    # Return a Flask response object with the generator function
    return Response(generate(), headers=headers, status=200)

# Route to display the table
@app.route('/')
def index():
    response = requests.get(url)

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
    
    # Create the table using Flask-Table
    table = ItemTable(items)

    # Render the HTML template with the table
    return render_template('index.html', table=table, name=name)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))