import base64
import os
from urllib.request import HTTPBasicAuthHandler
import requests
import logging
from getpass import getpass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

urls = [
    'https://regional-manager-eu-7nricgvmca-ew.a.run.app/',
    'https://regional-manager-us-7nricgvmca-uc.a.run.app/',
    'https://regional-manager-as-7nricgvmca-ts.a.run.app/'
]

regions = ['Europe', 'United States', 'Asia']


def upload_file(url, file_path, username, password):
    url = url + "files"
    logger.info(f'Uploading file: {file_path} to {url}')
    with open(file_path, 'rb') as file:
        credentials = base64.b64encode(f'{username}:{password}'.encode()).decode()
        headers = {'Authorization': f'Basic {credentials}'}
        response = requests.post(url, files={'file': file}, headers=headers)
        if response.status_code == requests.codes.ok:
            logger.info(f'File uploaded successfully to {url}')
        else:
            logger.error(f'File upload failed to {url}. Status code: {response.status_code}')

def select_region():
    print('Select a region:')
    for i, region in enumerate(regions):
        print(f'{i+1}. {region}')
    print(f'{len(regions) + 1}. All Regions')
    while True:
        try:
            choice = input('Enter the number corresponding to your choice (or q to quit): ')
            if choice == 'q':
                return None
            choice = int(choice)
            if 1 <= choice <= len(regions) + 1:
                return choice
            else:
                print('Invalid choice. Please try again.')
        except ValueError:
            print('Invalid input. Please enter a number.')

def main():
    logger.info('CLI program started.')
    
    while True:
        selected_region = select_region()
        if selected_region is None:
            break

        if selected_region == len(regions) + 1:
            selected_urls = urls
        else:
            selected_urls = [urls[selected_region - 1]]
        file_path = input('Enter the path of the file to upload (or q to go back to the region selection): ')
        if file_path == 'q':
            continue
        if not os.path.isfile(file_path):
            print('File does not exist. Please try again.')
            continue

        username = input('Enter your username: ')
        password = getpass('Enter your password: ')

        for url in selected_urls:
            try:
                upload_file(url, file_path, username, password)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 405:
                    print('HTTP 405 Method Not Allowed. Please try again.')
                    break
                else:
                    raise
        else:
            continue
        break

    logger.info('CLI program terminated.')

if __name__ == '__main__':
    main()
#/home/jx23/Desktop/noqueue.png