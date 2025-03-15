import os
import pytest
from unittest.mock import patch
from app.utils.config import Config
from app.services.playlist_service import PlaylistService
from app.models import AcestreamChannel
from app.repositories import ChannelRepository

@pytest.fixture
def config_with_base_url(monkeypatch):
    """Configure a base URL for testing."""
    config = Config()
    
    # Mock the base_url property to return a consistent value for tests
    monkeypatch.setattr(config, 'base_url', 'http://localhost:6878/ace/getstream?id=')
    
    return config

@pytest.fixture
def setup_test_channels(db_session):
    """Set up test channels for playlist tests."""
    # Create test channels with correct attribute name (id instead of channel_id)
    ch1 = AcestreamChannel(id='123', name='Sports Channel', group='Sports', logo='sports.png', is_online=True)
    ch2 = AcestreamChannel(id='456', name='News Channel', group='News', logo='news.png', is_online=True)
    db_session.add(ch1)
    db_session.add(ch2)
    db_session.commit()
    return [ch1, ch2]

@pytest.fixture(autouse=True)
def patch_playlist_service_config(monkeypatch, config_with_base_url):
    """Ensure PlaylistService uses our test config."""
    monkeypatch.setattr('app.services.playlist_service.Config', lambda: config_with_base_url)
    return config_with_base_url

def test_generate_playlist_with_search(db_session, setup_test_channels):
    """Test playlist generation with search filter."""
    # Create the service
    service = PlaylistService()
    
    # Generate playlist with search term
    playlist = service.generate_playlist(search_term='Sports')
    
    # Debug output
    print(f"Generated playlist: {playlist}")
    print(f"Expected URL fragment: http://localhost:6878/ace/getstream?id=123")
    
    # Verify correct URLs are in the playlist
    assert '123' in playlist
    assert '456' not in playlist

def test_generate_playlist_all_channels(db_session, setup_test_channels):
    """Test playlist generation with all channels."""
    service = PlaylistService()
    
    # Generate playlist with all channels
    playlist = service.generate_playlist()
    
    # Debug output
    print(f"Generated playlist: {playlist}")
    
    # Verify correct URLs are in the playlist
    assert '123' in playlist
    assert '456' in playlist

def test_format_stream_url_with_acexy(db_session, monkeypatch):
    """Test URL formatting when Acexy is enabled and port is 8080."""
    # Create service with custom base URL containing port 8080
    service = PlaylistService()
    
    # Mock the config to use Acexy port
    monkeypatch.setattr(service.config, 'base_url', 'http://localhost:8080/ace/getstream?id=')
    
    # Mock environment variable
    with patch.dict(os.environ, {"ENABLE_ACEXY": "true"}):
        # Format URL
        url = service._format_stream_url('abc123', 42)
        
        # Verify that no pid parameter is added
        assert url == 'http://localhost:8080/ace/getstream?id=abc123'
        assert '&pid=' not in url

def test_format_stream_url_without_acexy(db_session, monkeypatch):
    """Test URL formatting when Acexy is not enabled (default case)."""
    # Create service
    service = PlaylistService()
    
    # Mock the config to use standard port 6878
    monkeypatch.setattr(service.config, 'base_url', 'http://localhost:6878/ace/getstream?id=')
    
    # Format URL with Acexy disabled (default)
    url = service._format_stream_url('abc123', 42)
    
    # Verify that pid parameter is added
    assert url == 'http://localhost:6878/ace/getstream?id=abc123&pid=42'
    assert '&pid=42' in url

def test_format_stream_url_acexy_environment_overrides_port(db_session, monkeypatch):
    """Test that Acexy environment variable is respected even with 8080 port."""
    # Create service with port 8080 but Acexy explicitly disabled
    service = PlaylistService()
    
    # Mock the config to use Acexy port
    monkeypatch.setattr(service.config, 'base_url', 'http://localhost:8080/ace/getstream?id=')
    
    # Mock environment variable to explicitly disable Acexy
    with patch.dict(os.environ, {"ENABLE_ACEXY": "false"}):
        # Format URL
        url = service._format_stream_url('abc123', 42)
        
        # Should add pid parameter since ENABLE_ACEXY is false, despite port 8080
        assert url == 'http://localhost:8080/ace/getstream?id=abc123&pid=42'