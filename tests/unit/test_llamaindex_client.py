"""Unit tests for LlamaIndex client."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.integrations.llamaindex.client import LlamaIndexClient


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch('src.integrations.llamaindex.client.Settings') as mock:
        mock.LLAMACLOUD_API_KEY = "test_api_key"
        mock.LLAMACLOUD_BASE_URL = "https://api.cloud.llamaindex.ai"
        mock.LLAMACLOUD_INDEX_NAME = "test-index"
        mock.LLAMACLOUD_PROJECT_NAME = "Default"
        mock.LLAMACLOUD_ORGANIZATION_ID = "test-org-id"
        yield mock


@pytest.fixture
def client(mock_settings):
    """Create a LlamaIndex client for testing."""
    return LlamaIndexClient()


def test_init(client):
    """Test client initialization."""
    assert client.api_key == "test_api_key"
    assert client.base_url == "https://api.cloud.llamaindex.ai"
    assert client.index_name == "test-index"
    assert client.project_name == "Default"
    assert client.organization_id == "test-org-id"
    assert client.session is None
    assert not client.is_connected()


def test_init_no_api_key():
    """Test initialization fails without API key."""
    with patch('src.integrations.llamaindex.client.Settings') as mock:
        mock.LLAMACLOUD_API_KEY = ""
        mock.LLAMACLOUD_BASE_URL = "https://api.cloud.llamaindex.ai"
        mock.LLAMACLOUD_INDEX_NAME = "test-index"
        mock.LLAMACLOUD_PROJECT_NAME = "Default"
        mock.LLAMACLOUD_ORGANIZATION_ID = "test-org-id"
        with pytest.raises(ValueError, match="API key is required"):
            LlamaIndexClient()


@patch('src.integrations.llamaindex.client.requests.Session')
def test_connect_success(mock_session, client):
    """Test successful connection."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_session.return_value.get.return_value = mock_response

    result = client.connect()

    assert result is True
    assert client.is_connected()
    assert client.session is not None


@patch('src.integrations.llamaindex.client.requests.Session')
def test_connect_failure(mock_session, client):
    """Test connection failure."""
    mock_session.return_value.get.side_effect = Exception("Connection failed")

    result = client.connect()

    assert result is False
    assert not client.is_connected()


def test_disconnect(client):
    """Test disconnection."""
    client.session = Mock()
    client._connected = True

    result = client.disconnect()

    assert result is True
    assert not client.is_connected()
    assert client.session is None


def test_health_check_not_connected(client):
    """Test health check when not connected."""
    result = client.health_check()
    assert result is False


@patch('src.integrations.llamaindex.client.requests.Session')
def test_upload_documents_not_connected(mock_session, client):
    """Test upload fails when not connected."""
    documents = [{"content": "test", "metadata": {}}]

    with pytest.raises(RuntimeError, match="Not connected"):
        client.upload_documents(documents)


@patch('src.integrations.llamaindex.client.requests.Session')
def test_upload_documents_success(mock_session, client):
    """Test successful document upload."""
    client._connected = True
    client.session = Mock()

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "success"}
    client.session.post.return_value = mock_response

    documents = [
        {"content": "test content", "metadata": {}, "embedding": [0.1, 0.2, 0.3]}
    ]

    result = client.upload_documents(documents)

    assert result == {"status": "success"}
    client.session.post.assert_called_once()


def test_context_manager(mock_settings):
    """Test context manager functionality."""
    with patch('src.integrations.llamaindex.client.requests.Session') as mock_session:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_session.return_value.get.return_value = mock_response

        with LlamaIndexClient() as client:
            assert client.is_connected()

        assert not client.is_connected()
