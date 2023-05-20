import argparse
import datetime
import json
from urllib.parse import urljoin
import requests
import sys
from urllib.request import urlopen
from tqdm import tqdm
import math

def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def connect(cdn_url):
    try:
        response = requests.get(cdn_url)
        response.raise_for_status()
        json_data = response.json()
        ip = requests.get('http://ipinfo.io/json').json()['ip']
        print("External IP: ",ip)        
        print("Connecting to: ", cdn_url)
        print("Connected successfully!")
        print("Region: ", json_data['region'])
        print("CDN-Server-URL: ",json_data["cdn_url"])
        return json_data
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to the CDN service: {e}")
        return None


def fetch_data(url):
    if url.endswith("/"):
        url = url[:-1]  # Remove trailing "/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        for item in data:
            key = item["key"]
            last_modified = datetime.datetime.strptime(item["last_modified"], "%Y-%m-%dT%H:%M:%S.%fZ")
            size_in_bytes = int(item["size"])
            print(f"Key: {key}, Last Modified: {last_modified}, Size: {convert_size(size_in_bytes)}")
        print("Data fetched successfully.")
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return



def download_file(url_to_download, file_path):
    # download list of files
    # fetched_keys = [item["key"] for item in fetch_data(url_to_download)]
    # # check if filename is in the list
    # if file_path not in fetched_keys:
    #     print(f"Invalid filename. '{file_path}' is not a valid key in the fetched data.")
    #     return
    
    fullPath = urljoin(url_to_download, file_path)    
    try:
        with requests.get(fullPath, stream=True) as response:
            response.raise_for_status()
            total_size = int(response.headers.get('Content-Length', 0))
            print("total_size ", total_size)
            block_size = 4096

            with open(file_path, 'wb') as file, tqdm(total=total_size, unit='B', unit_scale=True) as pbar:
                for buffer in response.iter_content(block_size):
                    if not buffer:
                        break
                    file.write(buffer)
                    progress_bar_value = len(buffer)
                    pbar.update(len(buffer))
            print("File downloaded successfully.")
    except Exception as e:
        print(f"Error downloading file: {e}")

def main(cdn_url):
    # entry = input("CDN-API-URL: ")
    if cdn_url:
        cdn_url_obj = connect(cdn_url)
        cdn_url_edge = cdn_url_obj["cdn_url"] 
    else:
        print("CDN-API-URL is required.")
        return

    while True:

        command = input("Enter a command (fetch, download, exit): ")
        if command == "fetch":
            # url = input("Enter the URL: ")
            print("Fetching data from: ", cdn_url_edge)
            fetch_data(cdn_url_edge)
        elif command == "download":
            # url_to_download = input("Enter the URL to download: ")
            file_path = input("Enter the file name: ")
            download_file(cdn_url_edge, file_path)
        elif command == "exit":
            break
        else:
            print("Invalid command.")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CDN Download CLI")
    parser.add_argument("--cdn-url", type=str, help="CDN API URL")
    args = parser.parse_args()

    cdn_url = args.cdn_url

    if cdn_url:
        main(cdn_url)
    else:
        print("CDN-API-URL is required. Use --cdn-url to specify the URL.")
