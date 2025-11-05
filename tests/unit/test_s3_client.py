"""Unit tests for S3 client."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.integrations.s3.client import S3Client


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch('src.integrations.s3.client.Settings') as mock:
        mock.S3_BUCKET_NAME = "test-bucket"
        mock.AWS_ACCESS_KEY_ID = "test_access_key"
        mock.AWS_SECRET_ACCESS_KEY = "test_secret_key"
        mock.AWS_REGION = "us-east-1"
        yield mock


@pytest.fixture
def mock_boto3():
    """Mock boto3 module."""
    with patch('src.integrations.s3.client.boto3') as mock:
        yield mock


@pytest.fixture
def client(mock_settings, mock_boto3):
    """Create an S3 client for testing."""
    return S3Client()


def test_init(client):
    """Test client initialization."""
    assert client.bucket_name == "test-bucket"
    assert client.access_key_id == "test_access_key"
    assert client.secret_access_key == "test_secret_key"
    assert client.region_name == "us-east-1"
    assert client.s3_client is None
    assert not client.is_connected()


def test_connect_success(mock_boto3, client):
    """Test successful connection."""
    mock_s3_client = Mock()
    mock_s3_client.head_bucket.return_value = {}
    mock_boto3.client.return_value = mock_s3_client
    mock_boto3.resource.return_value = Mock()

    result = client.connect()

    assert result is True
    assert client.is_connected()
    mock_boto3.client.assert_called_once()
    mock_s3_client.head_bucket.assert_called_once_with(Bucket="test-bucket")


def test_connect_bucket_not_found(mock_boto3, client):
    """Test connection with non-existent bucket."""
    from botocore.exceptions import ClientError

    mock_s3_client = Mock()
    error_response = {'Error': {'Code': '404'}}
    mock_s3_client.head_bucket.side_effect = ClientError(error_response, 'head_bucket')
    mock_boto3.client.return_value = mock_s3_client
    mock_boto3.resource.return_value = Mock()

    result = client.connect()

    assert result is False
    assert not client.is_connected()


def test_disconnect(client):
    """Test disconnection."""
    client.s3_client = Mock()
    client.s3_resource = Mock()
    client._connected = True

    result = client.disconnect()

    assert result is True
    assert not client.is_connected()
    assert client.s3_client is None
    assert client.s3_resource is None


def test_upload_file_not_connected(client):
    """Test upload fails when not connected."""
    with pytest.raises(RuntimeError, match="Not connected"):
        client.upload_file(Path("/tmp/test.json"))


def test_upload_file_not_found(client):
    """Test upload fails when file doesn't exist."""
    client._connected = True
    client.s3_client = Mock()

    with pytest.raises(FileNotFoundError):
        client.upload_file(Path("/nonexistent/file.json"))


def test_upload_file_success(client, tmp_path):
    """Test successful file upload."""
    client._connected = True
    client.s3_client = Mock()

    # Create a temporary test file
    test_file = tmp_path / "test.json"
    test_file.write_text('{"test": "data"}')

    result = client.upload_file(test_file)

    assert result == "s3://test-bucket/test.json"
    client.s3_client.upload_file.assert_called_once()


def test_upload_file_with_custom_key(client, tmp_path):
    """Test file upload with custom S3 key."""
    client._connected = True
    client.s3_client = Mock()

    test_file = tmp_path / "test.json"
    test_file.write_text('{"test": "data"}')

    result = client.upload_file(test_file, s3_key="custom/path/file.json")

    assert result == "s3://test-bucket/custom/path/file.json"
    client.s3_client.upload_file.assert_called_once()


def test_download_file_not_connected(client):
    """Test download fails when not connected."""
    with pytest.raises(RuntimeError, match="Not connected"):
        client.download_file("test.json", Path("/tmp/test.json"))


def test_download_file_success(client, tmp_path):
    """Test successful file download."""
    client._connected = True
    client.s3_client = Mock()

    local_path = tmp_path / "downloaded.json"
    result = client.download_file("test.json", local_path)

    assert result == local_path
    client.s3_client.download_file.assert_called_once_with(
        "test-bucket",
        "test.json",
        str(local_path)
    )


def test_upload_json_success(client):
    """Test successful JSON upload."""
    client._connected = True
    client.s3_client = Mock()

    data = {"test": "data", "items": [1, 2, 3]}
    result = client.upload_json(data, "data.json")

    assert result == "s3://test-bucket/data.json"
    client.s3_client.put_object.assert_called_once()


def test_list_objects_success(client):
    """Test listing objects."""
    client._connected = True
    client.s3_client = Mock()

    mock_response = {
        'Contents': [
            {'Key': 'file1.json', 'Size': 100, 'LastModified': '2024-01-01', 'ETag': 'abc123'},
            {'Key': 'file2.json', 'Size': 200, 'LastModified': '2024-01-02', 'ETag': 'def456'}
        ]
    }
    client.s3_client.list_objects_v2.return_value = mock_response

    result = client.list_objects(prefix="embeddings/")

    assert len(result) == 2
    assert result[0]['key'] == 'file1.json'
    assert result[1]['key'] == 'file2.json'


def test_delete_object_success(client):
    """Test deleting an object."""
    client._connected = True
    client.s3_client = Mock()

    result = client.delete_object("test.json")

    assert result is True
    client.s3_client.delete_object.assert_called_once_with(
        Bucket="test-bucket",
        Key="test.json"
    )


def test_get_object_url(client):
    """Test generating presigned URL."""
    client._connected = True
    client.s3_client = Mock()
    client.s3_client.generate_presigned_url.return_value = "https://test-url.com"

    result = client.get_object_url("test.json", expiration=3600)

    assert result == "https://test-url.com"
    client.s3_client.generate_presigned_url.assert_called_once()


def test_context_manager(mock_settings, mock_boto3):
    """Test context manager functionality."""
    mock_s3_client = Mock()
    mock_s3_client.head_bucket.return_value = {}
    mock_boto3.client.return_value = mock_s3_client
    mock_boto3.resource.return_value = Mock()

    with S3Client() as client:
        assert client.is_connected()

    assert not client.is_connected()
