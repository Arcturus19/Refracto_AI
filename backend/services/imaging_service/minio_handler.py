"""
MinIO Handler for Image Storage
"""

from minio import Minio
from minio.error import S3Error
from io import BytesIO
from datetime import timedelta
from typing import Optional
from config import settings
import logging

logger = logging.getLogger(__name__)


class MinioHandler:
    """
    Handler class for MinIO object storage operations
    """
    
    def __init__(self):
        """Initialize MinIO client with configuration from settings"""
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = settings.MINIO_BUCKET
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self) -> bool:
        """
        Ensure the default bucket exists, create if it doesn't
        
        Returns:
            True if bucket exists or was created successfully
        """
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"✓ Created bucket: {self.bucket_name}")
            else:
                logger.info(f"✓ Bucket already exists: {self.bucket_name}")
            return True
        except S3Error as err:
            logger.error(f"✗ Error with bucket {self.bucket_name}: {err}")
            return False
    
    def upload_file(
        self,
        file_data: bytes,
        bucket_name: str,
        object_name: str,
        content_type: Optional[str] = None
    ) -> bool:
        """
        Upload file data to MinIO
        
        Args:
            file_data: Binary file data
            bucket_name: Target bucket name
            object_name: Name for the object in MinIO (path)
            content_type: MIME type of the file
            
        Returns:
            True if upload successful, False otherwise
        """
        try:
            # Ensure bucket exists
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
            
            # Upload the file
            self.client.put_object(
                bucket_name,
                object_name,
                BytesIO(file_data),
                length=len(file_data),
                content_type=content_type or "application/octet-stream"
            )
            
            logger.info(f"✓ Uploaded {object_name} to {bucket_name} ({len(file_data)} bytes)")
            return True
            
        except S3Error as err:
            logger.error(f"✗ Upload error for {object_name}: {err}")
            return False
    
    def get_file_url(
        self,
        bucket_name: str,
        object_name: str,
        expires_seconds: int = 3600
    ) -> Optional[str]:
        """
        Generate a presigned URL for accessing a file
        
        Args:
            bucket_name: Bucket name
            object_name: Object name (path)
            expires_seconds: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL string or None if error
        """
        try:
            url = self.client.presigned_get_object(
                bucket_name,
                object_name,
                expires=timedelta(seconds=expires_seconds)
            )
            logger.info(f"✓ Generated URL for {object_name} (expires in {expires_seconds}s)")
            return url
            
        except S3Error as err:
            logger.error(f"✗ Error generating URL for {object_name}: {err}")
            return None
    
    def delete_file(
        self,
        bucket_name: str,
        object_name: str
    ) -> bool:
        """
        Delete a file from MinIO
        
        Args:
            bucket_name: Bucket name
            object_name: Object name to delete
            
        Returns:
            True if deletion successful
        """
        try:
            self.client.remove_object(bucket_name, object_name)
            logger.info(f"✓ Deleted {object_name} from {bucket_name}")
            return True
            
        except S3Error as err:
            logger.error(f"✗ Delete error for {object_name}: {err}")
            return False
    
    def file_exists(
        self,
        bucket_name: str,
        object_name: str
    ) -> bool:
        """
        Check if a file exists in MinIO
        
        Args:
            bucket_name: Bucket name
            object_name: Object name
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            self.client.stat_object(bucket_name, object_name)
            return True
        except S3Error:
            return False


# Singleton instance
_minio_handler = None


def get_minio_handler() -> MinioHandler:
    """
    Get or create MinioHandler singleton instance
    
    Returns:
        MinioHandler instance
    """
    global _minio_handler
    if _minio_handler is None:
        _minio_handler = MinioHandler()
    return _minio_handler
