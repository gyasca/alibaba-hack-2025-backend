import oss2
import os
from datetime import datetime
from flask import current_app

def get_oss_bucket():
    """Initialize and return an OSS bucket instance"""
    auth = oss2.Auth(
        os.getenv('OSS_ACCESS_KEY_ID'),
        os.getenv('OSS_ACCESS_KEY_SECRET')
    )
    bucket = oss2.Bucket(
        auth,
        os.getenv('OSS_ENDPOINT'),
        os.getenv('OSS_BUCKET_NAME')
    )
    return bucket

def upload_to_oss(file_obj, filename):
    """Upload a file to OSS and return the public URL"""
    try:
        bucket = get_oss_bucket()
        
        # Generate unique path with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        oss_path = f'oha/{timestamp}_{filename}'
        
        # Upload file
        bucket.put_object(oss_path, file_obj)
        
        # Generate and return public URL
        url = get_oss_url(oss_path)
        return url
        
    except Exception as e:
        current_app.logger.error(f"Error uploading to OSS: {str(e)}")
        raise e

def get_oss_url(oss_path):
    """Generate public URL for OSS object"""
    return f"https://{os.getenv('OSS_BUCKET_NAME')}.{os.getenv('OSS_ENDPOINT')}/{oss_path}"

def delete_from_oss(oss_path):
    """Delete a file from OSS"""
    try:
        bucket = get_oss_bucket()
        bucket.delete_object(oss_path)
        return True
    except Exception as e:
        current_app.logger.error(f"Error deleting from OSS: {str(e)}")
        raise e

def get_oss_path_from_url(url):
    """Extract OSS path from full URL"""
    try:
        # URL format: https://bucket-name.endpoint/path
        parts = url.split(f"{os.getenv('OSS_BUCKET_NAME')}.{os.getenv('OSS_ENDPOINT')}/", 1)
        if len(parts) != 2:
            raise ValueError("Invalid OSS URL format")
        return parts[1]
    except Exception as e:
        current_app.logger.error(f"Error extracting OSS path from URL: {str(e)}")
        raise e