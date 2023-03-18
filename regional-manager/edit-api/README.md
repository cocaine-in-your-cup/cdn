# edit-api
API responsible for propagating data changes to all the buckets under its region.
## Enviroment variables required 

- GCP\_PROJECT\_ID: GCP project id.
- GOOGLE\_APPLICATION\_CREDENTIALS: Path to json OAuth2.0 service account credentials.
- REGION: e.g., EU,NA,AS,..
- FLASK\_SERVER\_HOST: IP to host the server
- FLASK\_SERVER\_PORT: Port to host the server
- CERT\_FOLDER: Path to the folder containing the certification files (cert.pem, key.pem)

Example Config:
```bash
GCP_PROJECT_ID="cloud-administration-cc4092"
GOOGLE_APPLICATION_CREDENTIALS="./storageCreds.json"
REGION="EU"
FLASK_SERVER_HOST="127.0.0.1"
FLASK_SERVER_PORT="8008"
CERT_FOLDER="./certs/
```