"""Unit tests for mcp_lancedb __init__.py module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from mcp_lancedb import (
    optimize_table,
    table_versions,
    get_index_stats,
    analyze_query_perf,
    __version__
)

@pytest.mark.unit
class TestInitModule:
    """Test the __init__.py module functions."""
    
    def test_version(self):
        """Test that version is properly defined."""
        assert __version__ == "0.1.0"
    
    @patch('mcp_lancedb.core.optimization.optimizer')
    def test_optimize_table(self, mock_optimizer):
        """Test optimize_table convenience function."""
        # Mock the optimizer to return a realistic response
        mock_optimizer.optimize_table_performance.return_value = {
            "status": "optimized",
            "recommendations": []
        }
        
        result = optimize_table("test_table")
        
        assert isinstance(result, dict)
        assert "status" in result
        mock_optimizer.optimize_table_performance.assert_called_once_with("test_table")
    
    @patch('mcp_lancedb.core.optimization.optimizer')
    def test_table_versions(self, mock_optimizer):
        """Test table_versions convenience function."""
        # Mock the optimizer to return a realistic response
        mock_optimizer.manage_table_versions.return_value = {
            "versions": ["v1", "v2"],
            "current": "v2"
        }
        
        result = table_versions("test_table")
        
        assert isinstance(result, dict)
        assert "versions" in result
        mock_optimizer.manage_table_versions.assert_called_once_with("test_table")

@pytest.mark.unit
class TestGetIndexStats:
    """Test the get_index_stats function."""
    
    @patch('mcp_lancedb.core.connection.get_table_cached')
    @patch('mcp_lancedb.core.connection.sanitize_table_name')
    def test_get_index_stats_success(self, mock_sanitize, mock_get_table):
        """Test successful index stats retrieval."""
        mock_table = Mock()
        mock_table.list_indices.return_value = ["index1", "index2"]
        mock_table.stats.return_value = {"rows": 100, "size": "1MB"}
        mock_table.index_stats.return_value = {
            "num_unindexed_rows": 0,
            "index_coverage": "100%"
        }
        
        mock_sanitize.return_value = "test_table"
        mock_get_table.return_value = mock_table
        
        result = get_index_stats("test_table")
        
        assert isinstance(result, dict)
        assert "indices" in result
        assert result["indices"] == ["index1", "index2"]
        assert "basic_stats" in result
        assert result["basic_stats"]["rows"] == 100
        assert "index_performance" in result
        assert result["index_performance"]["num_unindexed_rows"] == 0
        assert "index_coverage" in result
        assert result["index_coverage"] == "Excellent - all rows indexed"
    
    @patch('mcp_lancedb.core.connection.get_table_cached')
    @patch('mcp_lancedb.core.connection.sanitize_table_name')
    def test_get_index_stats_with_unindexed_rows(self, mock_sanitize, mock_get_table):
        """Test index stats when there are unindexed rows."""
        mock_table = Mock()
        mock_table.list_indices.return_value = ["index1"]
        mock_table.stats.return_value = {"rows": 100, "size": "1MB"}
        mock_table.index_stats.return_value = {
            "num_unindexed_rows": 25,
            "index_coverage": "75%"
        }
        
        mock_sanitize.return_value = "test_table"
        mock_get_table.return_value = mock_table
        
        result = get_index_stats("test_table")
        
        assert isinstance(result, dict)
        assert "optimization_needed" in result
        assert "25 unindexed rows detected" in result["optimization_needed"]
    
    @patch('mcp_lancedb.core.connection.get_table_cached')
    @patch('mcp_lancedb.core.connection.sanitize_table_name')
    def test_get_index_stats_index_stats_error(self, mock_sanitize, mock_get_table):
        """Test index stats when detailed stats fail."""
        mock_table = Mock()
        mock_table.list_indices.return_value = ["index1"]
        mock_table.stats.return_value = {"rows": 100}
        mock_table.index_stats.side_effect = Exception("Stats not available")
        
        mock_sanitize.return_value = "test_table"
        mock_get_table.return_value = mock_table
        
        result = get_index_stats("test_table")
        
        assert isinstance(result, dict)
        assert "indices" in result
        assert "index_performance" in result
        assert "Detailed stats not available" in result["index_performance"]
    
    @patch('mcp_lancedb.core.connection.get_table_cached')
    @patch('mcp_lancedb.core.connection.sanitize_table_name')
    def test_get_index_stats_table_error(self, mock_sanitize, mock_get_table):
        """Test index stats when table access fails."""
        mock_sanitize.return_value = "test_table"
        mock_get_table.side_effect = Exception("Table not found")
        
        result = get_index_stats("test_table")
        
        assert isinstance(result, dict)
        assert "error" in result
        assert "Table not found" in result["error"]

@pytest.mark.unit
class TestAnalyzeQueryPerf:
    """Test the analyze_query_perf function."""
    
    @patch('mcp_lancedb.core.connection.analyze_query_performance')
    @patch('mcp_lancedb.core.connection.sanitize_table_name')
    def test_analyze_query_perf_success(self, mock_sanitize, mock_analyze):
        """Test successful query performance analysis."""
        mock_analyze.return_value = {
            "execution_time": "0.1s",
            "memory_usage": "10MB",
            "optimization_suggestions": ["add_index"]
        }
        mock_sanitize.return_value = "test_table"
        
        result = analyze_query_perf("test_table", "test query", 10)
        
        assert isinstance(result, dict)
        assert "execution_time" in result
        assert result["execution_time"] == "0.1s"
        assert "memory_usage" in result
        assert result["memory_usage"] == "10MB"
        assert "optimization_suggestions" in result
        assert "add_index" in result["optimization_suggestions"]
        mock_analyze.assert_called_once()
    
    @patch('mcp_lancedb.core.connection.analyze_query_performance')
    @patch('mcp_lancedb.core.connection.sanitize_table_name')
    def test_analyze_query_perf_error(self, mock_sanitize, mock_analyze):
        """Test query performance analysis when it fails."""
        mock_sanitize.return_value = "test_table"
        mock_analyze.side_effect = Exception("Analysis failed")
        
        result = analyze_query_perf("test_table", "test query")
        
        assert isinstance(result, dict)
        assert "error" in result
        assert "Analysis failed" in result["error"]
    
    @patch('mcp_lancedb.core.connection.analyze_query_performance')
    @patch('mcp_lancedb.core.connection.sanitize_table_name')
    def test_analyze_query_perf_default_parameters(self, mock_sanitize, mock_analyze):
        """Test query performance analysis with default parameters."""
        mock_analyze.return_value = {"status": "analyzed"}
        mock_sanitize.return_value = "test_table"
        
        result = analyze_query_perf("test_table")
        
        assert isinstance(result, dict)
        assert "status" in result
        assert result["status"] == "analyzed"
        # Should use default query="test" and top_k=5
        mock_analyze.assert_called_once()

@pytest.mark.unit
class TestInitImports:
    """Test that all expected imports are available."""
    
    def test_table_management_imports(self):
        """Test that table management functions are imported."""
        from mcp_lancedb import (
            create_table,
            delete_table,
            list_tables,
            table_count,
            table_details,
            table_stats
        )
        
        # Just check they're callable (they'll be mocked in actual tests)
        assert callable(create_table)
        assert callable(delete_table)
        assert callable(list_tables)
        assert callable(table_count)
        assert callable(table_details)
        assert callable(table_stats)
    
    def test_document_management_imports(self):
        """Test that document management functions are imported."""
        from mcp_lancedb import (
            ingest_docs,
            update_documents,
            delete_documents
        )
        
        assert callable(ingest_docs)
        assert callable(update_documents)
        assert callable(delete_documents)
    
    def test_search_operations_imports(self):
        """Test that search operation functions are imported."""
        from mcp_lancedb import (
            query_table,
            hybrid_search
        )
        
        assert callable(query_table)
        assert callable(hybrid_search)
    
    def test_core_components_imports(self):
        """Test that core components are imported."""
        from mcp_lancedb import (
            LANCEDB_URI,
            TABLE_NAME,
            EMBEDDING_FUNCTION,
            MODEL_NAME,
            model,
            logger,
            get_connection,
            get_all_tables,
            get_table_cached,
            clear_table_cache,
            analyze_query_performance,
            Schema
        )
        
        # Check that these are defined (values may vary)
        assert LANCEDB_URI is not None
        assert TABLE_NAME is not None
        assert EMBEDDING_FUNCTION is not None
        assert MODEL_NAME is not None
        assert model is not None
        assert logger is not None
        assert callable(get_connection)
        assert callable(get_all_tables)
        assert callable(get_table_cached)
        assert callable(clear_table_cache)
        assert callable(analyze_query_performance)
        assert Schema is not None
    
    def test_entry_points_imports(self):
        """Test that entry point functions are imported."""
        from mcp_lancedb import (
            run_server,
            cli_main
        )
        
        assert callable(run_server)
        assert callable(cli_main) 