"""AWS S3 client for cloud storage."""

import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
import json

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    boto3 = None
    ClientError = Exception
    NoCredentialsError = Exception

from ..base import BaseIntegrationClient, retry_on_failure
from config.settings import Settings

logger = logging.getLogger(__name__)


class S3Client(BaseIntegrationClient):
    """Client for interacting with AWS S3."""

    def __init__(
        self,
        bucket_name: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        region_name: Optional[str] = None
    ):
        """
        Initialize S3 client.

        Args:
            bucket_name: S3 bucket name (from Settings if not provided)
            access_key_id: AWS access key ID (from Settings if not provided)
            secret_access_key: AWS secret access key (from Settings if not provided)
            region_name: AWS region (from Settings if not provided)
        """
        super().__init__()

        if boto3 is None:
            raise ImportError(
                "boto3 is not installed. "
                "Install it with: pip install boto3"
            )

        self.bucket_name = bucket_name or Settings.S3_BUCKET_NAME
        self.access_key_id = access_key_id or Settings.AWS_ACCESS_KEY_ID
        self.secret_access_key = secret_access_key or Settings.AWS_SECRET_ACCESS_KEY
        self.region_name = region_name or Settings.AWS_REGION

        self.s3_client = None
        self.s3_resource = None

    def connect(self) -> bool:
        """
        Establish connection to AWS S3.

        Returns:
            True if connection successful
        """
        try:
            self.logger.info(f"Connecting to AWS S3 bucket: {self.bucket_name}...")

            # Create S3 client
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name=self.region_name
            )

            # Create S3 resource for higher-level operations
            self.s3_resource = boto3.resource(
                's3',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name=self.region_name
            )

            # Test connection
            if self.health_check():
                self._connected = True
                self.logger.info("✅ Connected to AWS S3")
                return True
            else:
                self.logger.error("❌ S3 health check failed")
                return False

        except NoCredentialsError:
            self.logger.error("❌ AWS credentials not found")
            return False
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to S3: {e}")
            return False

    def disconnect(self) -> bool:
        """
        Close connection to AWS S3.

        Returns:
            True if disconnection successful
        """
        try:
            self.s3_client = None
            self.s3_resource = None
            self._connected = False
            self.logger.info("Disconnected from AWS S3")
            return True
        except Exception as e:
            self.logger.error(f"Error disconnecting from S3: {e}")
            return False

    @retry_on_failure(max_retries=3, delay=1.0)
    def health_check(self) -> bool:
        """
        Check if S3 bucket is accessible.

        Returns:
            True if service is healthy
        """
        try:
            if not self.s3_client:
                return False

            # Check if bucket exists and is accessible
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == '404':
                self.logger.warning(f"Bucket '{self.bucket_name}' does not exist")
            else:
                self.logger.warning(f"Health check failed: {e}")
            return False
        except Exception as e:
            self.logger.warning(f"Health check failed: {e}")
            return False

    @retry_on_failure(max_retries=3, delay=2.0)
    def upload_file(
        self,
        file_path: Path,
        s3_key: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Upload a file to S3.

        Args:
            file_path: Path to local file
            s3_key: S3 object key (defaults to filename)
            metadata: Optional metadata for the object

        Returns:
            S3 URI of uploaded file

        Raises:
            RuntimeError: If not connected
            FileNotFoundError: If file doesn't exist
        """
        if not self._connected:
            raise RuntimeError("Not connected to S3. Call connect() first.")

        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if s3_key is None:
            s3_key = file_path.name

        try:
            self.logger.info(f"Uploading {file_path.name} to s3://{self.bucket_name}/{s3_key}...")

            extra_args = {}
            if metadata:
                extra_args['Metadata'] = metadata

            self.s3_client.upload_file(
                str(file_path),
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )

            s3_uri = f"s3://{self.bucket_name}/{s3_key}"
            self.logger.info(f"✅ Uploaded to {s3_uri}")
            return s3_uri

        except Exception as e:
            self.logger.error(f"❌ Failed to upload file: {e}")
            raise

    @retry_on_failure(max_retries=3, delay=2.0)
    def download_file(
        self,
        s3_key: str,
        local_path: Path
    ) -> Path:
        """
        Download a file from S3.

        Args:
            s3_key: S3 object key
            local_path: Local path to save file

        Returns:
            Path to downloaded file

        Raises:
            RuntimeError: If not connected
        """
        if not self._connected:
            raise RuntimeError("Not connected to S3. Call connect() first.")

        try:
            local_path = Path(local_path)
            local_path.parent.mkdir(parents=True, exist_ok=True)

            self.logger.info(f"Downloading s3://{self.bucket_name}/{s3_key}...")

            self.s3_client.download_file(
                self.bucket_name,
                s3_key,
                str(local_path)
            )

            self.logger.info(f"✅ Downloaded to {local_path}")
            return local_path

        except Exception as e:
            self.logger.error(f"❌ Failed to download file: {e}")
            raise

    @retry_on_failure(max_retries=3, delay=2.0)
    def upload_json(
        self,
        data: Any,
        s3_key: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Upload JSON data directly to S3.

        Args:
            data: Data to serialize as JSON
            s3_key: S3 object key
            metadata: Optional metadata

        Returns:
            S3 URI of uploaded object
        """
        if not self._connected:
            raise RuntimeError("Not connected to S3. Call connect() first.")

        try:
            self.logger.info(f"Uploading JSON to s3://{self.bucket_name}/{s3_key}...")

            json_data = json.dumps(data, ensure_ascii=False)

            extra_args = {'ContentType': 'application/json'}
            if metadata:
                extra_args['Metadata'] = metadata

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json_data.encode('utf-8'),
                **extra_args
            )

            s3_uri = f"s3://{self.bucket_name}/{s3_key}"
            self.logger.info(f"✅ Uploaded JSON to {s3_uri}")
            return s3_uri

        except Exception as e:
            self.logger.error(f"❌ Failed to upload JSON: {e}")
            raise

    @retry_on_failure(max_retries=3, delay=2.0)
    def list_objects(
        self,
        prefix: str = "",
        max_keys: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        List objects in S3 bucket.

        Args:
            prefix: Filter objects by prefix
            max_keys: Maximum number of objects to return

        Returns:
            List of object metadata dictionaries
        """
        if not self._connected:
            raise RuntimeError("Not connected to S3. Call connect() first.")

        try:
            self.logger.debug(f"Listing objects with prefix '{prefix}'...")

            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )

            objects = []
            for obj in response.get('Contents', []):
                objects.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'etag': obj['ETag']
                })

            self.logger.debug(f"Found {len(objects)} objects")
            return objects

        except Exception as e:
            self.logger.error(f"❌ Failed to list objects: {e}")
            raise

    @retry_on_failure(max_retries=3, delay=2.0)
    def delete_object(self, s3_key: str) -> bool:
        """
        Delete an object from S3.

        Args:
            s3_key: S3 object key

        Returns:
            True if deletion successful
        """
        if not self._connected:
            raise RuntimeError("Not connected to S3. Call connect() first.")

        try:
            self.logger.info(f"Deleting s3://{self.bucket_name}/{s3_key}...")

            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )

            self.logger.info(f"✅ Deleted {s3_key}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to delete object: {e}")
            raise

    def get_object_url(self, s3_key: str, expiration: int = 3600) -> str:
        """
        Generate a presigned URL for an S3 object.

        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)

        Returns:
            Presigned URL
        """
        if not self._connected:
            raise RuntimeError("Not connected to S3. Call connect() first.")

        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )

            self.logger.debug(f"Generated presigned URL for {s3_key}")
            return url

        except Exception as e:
            self.logger.error(f"❌ Failed to generate presigned URL: {e}")
            raise
