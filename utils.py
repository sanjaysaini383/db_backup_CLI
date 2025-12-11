import logging
import tarfile
import gzip
import os
import shutil
import boto3
from google.cloud import storage as gcs
from azure.storage.blob import BlobServiceClient
import requests
import json

# ============= LOGGING =============
def setup_logging(log_file='backup.log'):
    """Setup logging configuration"""
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Also log to console
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logging.getLogger('').addHandler(console)
    
    logging.info(f"Logging initialized: {log_file}")
    return logging.getLogger('')

# ============= COMPRESSION =============
def compress_backup(backup_file, output_file, logger):
    """Compress backup file to tar.gz"""
    try:
        if not os.path.isfile(backup_file):
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        
        with tarfile.open(output_file, "w:gz") as tar:
            tar.add(backup_file, arcname=os.path.basename(backup_file))
        
        logger.info(f"Compressed: {output_file}")
        os.remove(backup_file)  # Remove original
        return output_file
    
    except Exception as e:
        logger.error(f"Compression failed: {e}")
        raise

def decompress_backup(backup_file):
    """Decompress backup file"""
    if backup_file.endswith('.tar.gz'):
        decompressed = backup_file[:-7]
        with tarfile.open(backup_file, "r:gz") as tar:
            tar.extractall(path=os.path.dirname(backup_file))
        return decompressed
    
    elif backup_file.endswith('.gz'):
        decompressed = backup_file[:-3]
        with gzip.open(backup_file, 'rb') as f_in:
            with open(decompressed, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        return decompressed
    
    return backup_file


# ============= CLOUD STORAGE =============
def upload_to_cloud(provider, local_file, bucket_name, config, logger):
    """Upload backup to cloud storage"""
    try:
        if provider == 's3':
            session = boto3.Session(
                aws_access_key_id=config['aws']['access_key'],
                aws_secret_access_key=config['aws']['secret_key'],
                region_name=config['aws']['region']
            )
            s3 = session.client('s3')
            s3.upload_file(local_file, bucket_name, os.path.basename(local_file))
            logger.info(f"Uploaded to S3: {bucket_name}")
        
        elif provider == 'gcs':
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config['gcs']['service_account_key']
            client = gcs.Client()
            bucket = client.get_bucket(bucket_name)
            blob = bucket.blob(os.path.basename(local_file))
            blob.upload_from_filename(local_file)
            logger.info(f"Uploaded to GCS: {bucket_name}")
        
        elif provider == 'azure':
            blob_service = BlobServiceClient.from_connection_string(
                config['azure']['connection_string']
            )
            blob_client = blob_service.get_blob_client(
                container=bucket_name,
                blob=os.path.basename(local_file)
            )
            with open(local_file, "rb") as data:
                blob_client.upload_blob(data)
            logger.info(f"Uploaded to Azure: {bucket_name}")
    
    except Exception as e:
        logger.error(f"Cloud upload failed: {e}")
        raise


# ============= NOTIFICATIONS =============
def send_slack_notification(webhook_url, message, logger):
    """Send Slack notification"""
    try:
        response = requests.post(
            webhook_url,
            data=json.dumps({'text': message}),
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            logger.info(f"Slack notification sent: {message}")
        else:
            logger.error(f"Slack error {response.status_code}: {response.text}")
    
    except Exception as e:
        logger.error(f"Notification failed: {e}")