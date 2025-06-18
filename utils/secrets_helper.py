import os
from google.cloud import secretmanager
from dotenv import load_dotenv

def get_secret(secret_name, env_var_name=None):
    """
    Get secret from environment variable (local) or Secret Manager (cloud)
    """
    # Try environment variable first
    load_dotenv()
    value = os.getenv(env_var_name or secret_name.upper().replace('-', '_'))
    
    if value:
        return value
    
    # Try Secret Manager
    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "devpost-ai-in-action")
        secret_path = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": secret_path})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"Could not load secret {secret_name}: {e}")
        return None