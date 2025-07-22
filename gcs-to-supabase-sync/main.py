import functions_framework
from cloudevents.http import CloudEvent
from google.cloud import storage
from google.cloud import secretmanager
from supabase import create_client, Client
import os

PROJECT_ID = os.environ.get('GCP_PROJECT', 'fake-profile-detection-460117')

def get_supabase_key():
    """Fetch the Supabase service_role key from Secret Manager"""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/supabase-service-role-key/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode('UTF-8')

def get_supabase_client() -> Client:
    """Initialize Supabase client with service_role key"""
    service_key = get_supabase_key()
    supabase_url = os.environ.get('SUPABASE_URL')
    return create_client(supabase_url, service_key)

@functions_framework.cloud_event
def process_gcs_file(cloud_event: CloudEvent) -> None:
    """
    Triggered when a file is uploaded to uploads/ directory in GCS bucket.
    Downloads from GCS and uploads to Supabase.
    """
    data = cloud_event.data
    file_name = data["name"]
    bucket_name = data["bucket"]
    
    # Only process files in uploads/ directory
    if not file_name.startswith("uploads/"):
        print(f"Skipping file outside uploads/: {file_name}")
        return
    
    print(f"Processing file: {file_name}")
    
    try:
        # 1) Download file from GCS
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        file_content = blob.download_as_bytes()
        print(f"Downloaded {len(file_content)} bytes from GCS")
        
        # 2) Initialize Supabase client
        supabase = get_supabase_client()
        
        # 3) Extract relative filename (remove "uploads/" prefix)
        relative_name = file_name[8:]  # Remove "uploads/"
        
        # 4) Upload to Supabase Storage - KEEP THE UPLOADS PREFIX!
        supabase_bucket = os.environ.get('SUPABASE_BUCKET_NAME', 'data-collection-files')
        supabase_path = f"uploads/{relative_name}"  # Add uploads/ back
        
        # Upload the file
        response = supabase.storage.from_(supabase_bucket).upload(
            path=supabase_path,
            file=file_content,
            file_options={
                "content-type": data.get('contentType', 'application/octet-stream'),
                "upsert": "true"
            }
        )
        
        print(f"✓ Successfully synced {file_name} to Supabase as {supabase_path}")
        print(f"Response: {response}")
        
    except Exception as e:
        print(f"✗ Error syncing {file_name}: {str(e)}")
        import traceback
        traceback.print_exc()