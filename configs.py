import json
import os
from google.cloud import secretmanager
from google.oauth2 import service_account

try:
    # Load the service account key file
    with open(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'), "r") as f:
        service_account_info = json.load(f)

    # Create credentials
    credentials = service_account.Credentials.from_service_account_info(
        service_account_info
    )
except:
    pass

def get_secret(secret_name):
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.environ.get("GOOGLE_PROJECT_ID")  # Ensure you have your GCP project ID as an env variable
    if not project_id:
        raise ValueError("GOOGLE_PROJECT_ID environment variable not set.")

    secret_version_name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"

    try:
        response = client.access_secret_version(request={"name": secret_version_name})
        secret_content = response.payload.data.decode("utf-8")
        # Assuming your secret content is a JSON key file
        credentials_info = json.loads(secret_content)
    except Exception as e:
        print(f"Error accessing secret '{secret_name}': {e}")
        # Handle the error appropriately, perhaps by raising it
        raise

    return credentials_info
