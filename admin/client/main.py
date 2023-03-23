from werkzeug.utils import secure_filename
import requests
import sys

def upload(url: str, file_name: str) -> None:
    """
    Upload a file via a POST request
    """
    # 'http://127.0.0.1:8008/files'
    file_name = secure_filename(file_name)
    with open(file_name, 'rb') as f:
        r = requests.post(url, files={'file': f}, verify=False)
        if r.ok:
            print(f"Uploaded {f.name}")
        else:
            print(r.text)

if len(sys.argv) < 3:
    print("Insuficient Arguments")
else:
    match sys.argv[1]:
        case "UPLOAD":
            upload('https://127.0.0.1:8008/files', sys.argv[2])

        case "DELETE":
            print("You can become a Data Scientist")
        case _:
            print("INVALID")