"""
MinIO Object Storage Client Configuration
Utility functions for interacting with MinIO for medical image storage
"""

from minio import Minio
from minio.error import S3Error
from typing import Optional, BinaryIO
import os


class MinIOClient:
    """
    MinIO client wrapper for object storage operations
    """
    
    def __init__(
        self,
        endpoint: str = "localhost:9000",
        access_key: str | None = None,
        secret_key: str | None = None,
        secure: bool = False
    ):
        """
        Initialize MinIO client
        
        Args:
            endpoint: MinIO server endpoint (default: localhost:9000)
            access_key: MinIO root user
            secret_key: MinIO root password
            secure: Use HTTPS (default: False for local development)
        """
        if not access_key or not secret_key:
            raise ValueError("MINIO_ROOT_USER and MINIO_ROOT_PASSWORD must be configured")

        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
    
    def ensure_bucket_exists(self, bucket_name: str) -> bool:
        """
        Ensure a bucket exists, create if it doesn't
        
        Args:
            bucket_name: Name of the bucket
            
        Returns:
            True if bucket exists or was created successfully
        """
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                print(f"✓ Created bucket: {bucket_name}")
            return True
        except S3Error as err:
            print(f"✗ Error with bucket {bucket_name}: {err}")
            return False
    
    def upload_file(
        self,
        bucket_name: str,
        object_name: str,
        file_path: str,
        content_type: Optional[str] = None
    ) -> bool:
        """
        Upload a file to MinIO
        
        Args:
            bucket_name: Target bucket name
            object_name: Name for the object in MinIO
            file_path: Path to the file to upload
            content_type: MIME type of the file (optional)
            
        Returns:
            True if upload successful
        """
        try:
            self.client.fput_object(
                bucket_name,
                object_name,
                file_path,
                content_type=content_type
            )
            print(f"✓ Uploaded {object_name} to {bucket_name}")
            return True
        except S3Error as err:
            print(f"✗ Upload error: {err}")
            return False
    
    def upload_bytes(
        self,
        bucket_name: str,
        object_name: str,
        data: bytes,
        content_type: Optional[str] = None
    ) -> bool:
        """
        Upload bytes data to MinIO
        
        Args:
            bucket_name: Target bucket name
            object_name: Name for the object in MinIO
            data: Bytes data to upload
            content_type: MIME type of the data (optional)
            
        Returns:
            True if upload successful
        """
        try:
            from io import BytesIO
            
            self.client.put_object(
                bucket_name,
                object_name,
                BytesIO(data),
                length=len(data),
                content_type=content_type
            )
            print(f"✓ Uploaded {object_name} to {bucket_name}")
            return True
        except S3Error as err:
            print(f"✗ Upload error: {err}")
            return False
    
    def download_file(
        self,
        bucket_name: str,
        object_name: str,
        file_path: str
    ) -> bool:
        """
        Download a file from MinIO
        
        Args:
            bucket_name: Source bucket name
            object_name: Name of the object in MinIO
            file_path: Path where to save the file
            
        Returns:
            True if download successful
        """
        try:
            self.client.fget_object(
                bucket_name,
                object_name,
                file_path
            )
            print(f"✓ Downloaded {object_name} from {bucket_name}")
            return True
        except S3Error as err:
            print(f"✗ Download error: {err}")
            return False
    
    def get_object_url(
        self,
        bucket_name: str,
        object_name: str,
        expires_seconds: int = 3600
    ) -> Optional[str]:
        """
        Get a presigned URL for an object
        
        Args:
            bucket_name: Bucket name
            object_name: Object name
            expires_seconds: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL string or None if error
        """
        try:
            from datetime import timedelta
            
            url = self.client.presigned_get_object(
                bucket_name,
                object_name,
                expires=timedelta(seconds=expires_seconds)
            )
            return url
        except S3Error as err:
            print(f"✗ Error generating URL: {err}")
            return None
    
    def delete_object(
        self,
        bucket_name: str,
        object_name: str
    ) -> bool:
        """
        Delete an object from MinIO
        
        Args:
            bucket_name: Bucket name
            object_name: Object name to delete
            
        Returns:
            True if deletion successful
        """
        try:
            self.client.remove_object(bucket_name, object_name)
            print(f"✓ Deleted {object_name} from {bucket_name}")
            return True
        except S3Error as err:
            print(f"✗ Delete error: {err}")
            return False
    
    def list_objects(
        self,
        bucket_name: str,
        prefix: Optional[str] = None
    ) -> list:
        """
        List objects in a bucket
        
        Args:
            bucket_name: Bucket name
            prefix: Filter by prefix (optional)
            
        Returns:
            List of object names
        """
        try:
            objects = self.client.list_objects(
                bucket_name,
                prefix=prefix,
                recursive=True
            )
            return [obj.object_name for obj in objects]
        except S3Error as err:
            print(f"✗ List error: {err}")
            return []


# Singleton instance for easy import
def get_minio_client() -> MinIOClient:
    """
    Get or create MinIO client instance
    
    Returns:
        MinIOClient instance
    """
    # In production, load these from environment variables
    endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    access_key = os.getenv("MINIO_ROOT_USER")
    secret_key = os.getenv("MINIO_ROOT_PASSWORD")
    secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
    
    return MinIOClient(
        endpoint=endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=secure
    )
