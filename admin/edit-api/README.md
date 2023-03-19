# edit-api
API responsible for propagating data changes to all the Regional Managers.
## Enviroment variables required 

- GCP\_PROJECT\_ID: GCP project id.
- GOOGLE\_APPLICATION\_CREDENTIALS: Path to json OAuth2.0 service account credentials.
- REGION: e.g., EU,NA,AS,..
- FLASK\_SERVER\_HOST: IP to host the server
- FLASK\_SERVER\_PORT: Port to host the server
- CERT\_FOLDER: Path to the folder containing the certification files (cert.pem, key.pem)
- REGIONAL\_MANAGERS\_API\_PORT: Port of the Regional Managers edit-api.

Example Config:
```bash
GCP_PROJECT_ID="cloud-administration-cc4092"
GOOGLE_APPLICATION_CREDENTIALS="./service-account-oauth2.json"
REGION="EU"
FLASK_SERVER_HOST="127.0.0.1"
FLASK_SERVER_PORT="8007"
CERT_FOLDER="./certs/"
REGIONAL_MANAGERS_API_PORT="8008"
```

## GCP Service Account
To execute this server a Oauth2.0 token of the **Admin Client API** service account is required.
