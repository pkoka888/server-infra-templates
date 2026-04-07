"""
Tests for Metabase pipeline scripts.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


class TestPipeline:
    """Test pipeline functionality."""

    @pytest.fixture
    def mock_env(self, tmp_path):
        """Create temp env file for testing."""
        env_file = tmp_path / ".env.test"
        env_file.write_text("""
POSTGRES_HOST=metabase-db
POSTGRES_PORT=5432
POSTGRES_USER=test
POSTGRES_PASSWORD=test
POSTGRES_DATABASE=test
""")
        return tmp_path

    def test_get_client_env(self, mock_env):
        """Test loading client environment variables."""
        os.chdir(mock_env)

        # Create client env file
        client_env = mock_env / ".env.client1"
        client_env.write_text("CLIENT_ID=client1\nGA4_PROPERTY_ID=123\n")

        # Import after setting up files
        import importlib
        import pipeline

        importlib.reload(pipeline)

        env = pipeline.get_client_env("client1")
        assert env.get("CLIENT_ID") == "client1"
        assert env.get("GA4_PROPERTY_ID") == "123"


class TestMetabaseAPI:
    """Test Metabase API client."""

    def test_api_health_check(self):
        """Test health check endpoint."""
        # This would require actual Metabase running
        # For now, just test the import
        from pipeline import run_ga4_pipeline

        assert run_ga4_pipeline is not None


class TestClients:
    """Test client configuration."""

    def test_example_client_exists(self):
        """Test that example client file exists."""
        example_path = os.path.join(os.path.dirname(__file__), "..", "scripts", ".env.example")
        assert os.path.exists(example_path), ".env.example should exist"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
