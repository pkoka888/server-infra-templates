"""
Tests for LangGraph ETL integration.
"""

import os
import pytest
from unittest.mock import patch, MagicMock


class TestLangGraphETL:
    """Test LangGraph ETL workflow."""

    def test_langgraph_etl_import(self):
        """Test that langgraph_etl module can be imported."""
        # Just test import doesn't crash
        import langgraph_etl

        assert langgraph_etl is not None

    def test_fallback_mode(self):
        """Test that fallback mode works when LangGraph unavailable."""
        import langgraph_etl

        # Mock LangGraph as unavailable
        with patch.object(langgraph_etl, "LANGGRAPH_AVAILABLE", False):
            result = langgraph_etl.run_etl_workflow("test_client", ["ga4"])
            assert result["mode"] == "fallback"
            assert "client_id" in result


class TestLangGraphClient:
    """Test LangGraph client integration."""

    def test_client_methods_exist(self):
        """Test that client has required methods."""
        from langgraph_client import LangGraphClient

        client = LangGraphClient()
        assert hasattr(client, "health_check")
        assert hasattr(client, "run_audit")
        assert hasattr(client, "validate_dataset")
        assert hasattr(client, "log_event")
        assert hasattr(client, "run_etl")


class TestPipelineIntegration:
    """Test pipeline integration with LangGraph."""

    def test_langgraph_import_in_pipeline(self):
        """Test that pipeline can import LangGraph client."""
        import pipeline

        # Check the flag exists
        assert hasattr(pipeline, "LANGGRAPH_AVAILABLE")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
