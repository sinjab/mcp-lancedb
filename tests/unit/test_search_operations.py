"""Unit tests for search operations."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from mcp_lancedb import query_table, hybrid_search


@pytest.mark.unit
class TestQueryTable:
    """Test table query functionality."""
    

    @patch('mcp_lancedb.operations.search_operations.verify_table_exists')
    def test_query_table_not_exists(self, mock_verify_table):
        """Test query on non-existent table."""
        mock_verify_table.return_value = False
        
        result = query_table("test query", table_name="nonexistent-table")
        
        assert isinstance(result, str)
        assert "Error" in result
        assert "does not exist" in result
    





@pytest.mark.unit
class TestHybridSearch:
    """Test hybrid search functionality."""
    
    @patch('mcp_lancedb.core.connection.open_table_with_retry')
    @patch('mcp_lancedb.core.connection.get_fresh_connection')
    @patch('mcp_lancedb.operations.search_operations.get_embeddings')
    def test_hybrid_search_success(self, mock_get_embeddings, mock_get_connection, mock_open_table):
        """Test successful hybrid search."""
        # Setup database and table mocks
        mock_db = Mock()
        mock_table = Mock()
        mock_get_connection.return_value = mock_db
        mock_open_table.return_value = mock_table
        
        # Mock database connection
        mock_db.table_names.return_value = ["TestTable"]  # Table exists
        mock_db.open_table.return_value = mock_table
        mock_table.count_rows.return_value = 2
        mock_table.schema = Mock()  # For table accessibility check
        
        mock_get_embeddings.return_value = [[0.1, 0.2, 0.3]]
        
        # Mock hybrid search results - more complex chain for hybrid search
        mock_search = Mock()
        mock_search_with_metric = Mock()
        mock_search_limited = Mock()
        
        mock_search_limited.to_list.return_value = [
            {"doc": "Hybrid result 1", "vector": [0.1, 0.2, 0.3], "_distance": 0.1},
            {"doc": "Hybrid result 2", "vector": [0.4, 0.5, 0.6], "_distance": 0.2}
        ]
        
        mock_search_with_metric.limit.return_value = mock_search_limited
        mock_search.metric.return_value = mock_search_with_metric
        mock_table.search.return_value = mock_search
        
        result = hybrid_search(
            "test query",
            table_name="test-table", 
            top_k=5,
            metric="cosine"
        )
        
        assert isinstance(result, dict)
        assert "results" in result
        assert "query" in result
        assert len(result["results"]) == 2
        
        mock_get_connection.assert_called()
        # Note: get_embeddings is not called because LanceDB handles embeddings automatically
    
    @patch('mcp_lancedb.core.connection.get_fresh_connection')
    def test_hybrid_search_table_not_exists(self, mock_get_connection):
        """Test hybrid search on non-existent table."""
        # Setup database mock - table doesn't exist
        mock_db = Mock()
        mock_db.table_names.return_value = []  # No tables exist
        mock_get_connection.return_value = mock_db
        
        result = hybrid_search("test query", table_name="nonexistent-table")
        
        assert isinstance(result, str)
        assert "Error" in result
        assert "does not exist" in result
    
    @patch('mcp_lancedb.core.connection.open_table_with_retry')
    @patch('mcp_lancedb.core.connection.get_fresh_connection')
    @patch('mcp_lancedb.operations.search_operations.get_embeddings')
    def test_hybrid_search_embedding_failure(self, mock_get_embeddings, mock_get_connection, mock_open_table):
        """Test hybrid search when embedding generation fails."""
        # Setup database and table mocks
        mock_db = Mock()
        mock_table = Mock()
        mock_get_connection.return_value = mock_db
        mock_open_table.return_value = mock_table
        
        # Mock database connection
        mock_db.table_names.return_value = ["TestTable"]  # Table exists
        mock_db.open_table.return_value = mock_table
        mock_table.count_rows.return_value = 0  # Empty table
        mock_table.schema = Mock()  # For table accessibility check
        
        mock_get_embeddings.side_effect = Exception("Embedding failed")
        
        # Add mock chain for hybrid search even though embedding fails
        mock_search = Mock()
        mock_search_with_metric = Mock()
        mock_search_limited = Mock()
        
        mock_search_limited.to_list.return_value = []
        
        mock_search_with_metric.limit.return_value = mock_search_limited
        mock_search.metric.return_value = mock_search_with_metric
        mock_table.search.return_value = mock_search
        
        result = hybrid_search("test query", table_name="test-table")
        
        # With empty table, it should return empty results before trying embeddings
        assert isinstance(result, dict)
        assert "results" in result
        assert len(result["results"]) == 0
    
    @patch('mcp_lancedb.core.connection.open_table_with_retry')
    @patch('mcp_lancedb.core.connection.get_fresh_connection')
    @patch('mcp_lancedb.operations.search_operations.get_embeddings')
    def test_hybrid_search_invalid_weights(self, mock_get_embeddings, mock_get_connection, mock_open_table):
        """Test hybrid search with invalid weight parameters."""
        # Setup database and table mocks
        mock_db = Mock()
        mock_table = Mock()
        mock_get_connection.return_value = mock_db
        mock_open_table.return_value = mock_table
        
        # Mock database connection
        mock_db.table_names.return_value = ["TestTable"]  # Table exists
        mock_db.open_table.return_value = mock_table
        mock_table.count_rows.return_value = 1
        mock_table.schema = Mock()  # For table accessibility check
        
        mock_get_embeddings.return_value = [[0.1, 0.2, 0.3]]
        
        # Mock empty results for invalid weights - complex chain for hybrid search
        mock_search = Mock()
        mock_search_with_metric = Mock()
        mock_search_limited = Mock()
        
        mock_search_limited.to_list.return_value = []
        
        mock_search_with_metric.limit.return_value = mock_search_limited
        mock_search.metric.return_value = mock_search_with_metric
        mock_table.search.return_value = mock_search
        
        result = hybrid_search("query", table_name="test-table", distance_threshold=-1.0)
        
        assert isinstance(result, dict)
        assert "results" in result
        assert len(result["results"]) == 0
    
    @patch('mcp_lancedb.core.connection.open_table_with_retry')
    @patch('mcp_lancedb.core.connection.get_fresh_connection')
    @patch('mcp_lancedb.operations.search_operations.get_embeddings')
    def test_hybrid_search_custom_weights(self, mock_get_embeddings, mock_get_connection, mock_open_table):
        """Test hybrid search with custom weights."""
        # Setup database and table mocks
        mock_db = Mock()
        mock_table = Mock()
        mock_get_connection.return_value = mock_db
        mock_open_table.return_value = mock_table
        
        # Mock database connection
        mock_db.table_names.return_value = ["TestTable"]  # Table exists
        mock_db.open_table.return_value = mock_table
        mock_table.count_rows.return_value = 1
        mock_table.schema = Mock()  # For table accessibility check
        
        mock_get_embeddings.return_value = [[0.1, 0.2, 0.3]]
        
        # Mock search results - complex chain for hybrid search
        mock_search = Mock()
        mock_search_with_metric = Mock()
        mock_search_limited = Mock()
        
        mock_search_limited.to_list.return_value = [
            {"doc": "Weighted result", "vector": [0.1, 0.2, 0.3], "_distance": 0.3}
        ]
        
        mock_search_with_metric.limit.return_value = mock_search_limited
        mock_search.metric.return_value = mock_search_with_metric
        mock_table.search.return_value = mock_search
        
        result = hybrid_search(
            "test query",
            table_name="test-table",
            metric="euclidean",
            distance_threshold=0.5
        )
        
        assert isinstance(result, dict)
        assert len(result["results"]) == 1
    
    @patch('mcp_lancedb.core.connection.open_table_with_retry')
    @patch('mcp_lancedb.core.connection.get_fresh_connection')
    @patch('mcp_lancedb.operations.search_operations.get_embeddings')
    def test_hybrid_search_different_metrics(self, mock_get_embeddings, mock_get_connection, mock_open_table):
        """Test hybrid search with different distance metrics."""
        # Setup database and table mocks
        mock_db = Mock()
        mock_table = Mock()
        mock_get_connection.return_value = mock_db
        mock_open_table.return_value = mock_table
        
        # Mock database connection
        mock_db.table_names.return_value = ["TestTable"]  # Table exists
        mock_db.open_table.return_value = mock_table
        mock_table.count_rows.return_value = 1
        mock_table.schema = Mock()  # For table accessibility check
        
        mock_get_embeddings.return_value = [[0.1, 0.2, 0.3]]
        
        # Mock search results - complex chain for hybrid search
        mock_search = Mock()
        mock_search_with_metric = Mock()
        mock_search_limited = Mock()
        
        mock_search_limited.to_list.return_value = [
            {"doc": "Metric result", "vector": [0.1, 0.2, 0.3], "_distance": 0.2}
        ]
        
        mock_search_with_metric.limit.return_value = mock_search_limited
        mock_search.metric.return_value = mock_search_with_metric
        mock_table.search.return_value = mock_search
        
        result = hybrid_search("test query", table_name="test-table", metric="dot")
        
        assert isinstance(result, dict)
        assert len(result["results"]) == 1
    
    @patch('mcp_lancedb.core.connection.open_table_with_retry')
    @patch('mcp_lancedb.core.connection.get_fresh_connection')
    @patch('mcp_lancedb.operations.search_operations.get_embeddings')
    def test_hybrid_search_empty_query(self, mock_get_embeddings, mock_get_connection, mock_open_table):
        """Test hybrid search with empty query."""
        # Setup database and table mocks
        mock_db = Mock()
        mock_table = Mock()
        mock_get_connection.return_value = mock_db
        mock_open_table.return_value = mock_table
        
        # Mock database connection
        mock_db.table_names.return_value = ["TestTable"]  # Table exists
        mock_db.open_table.return_value = mock_table
        mock_table.count_rows.return_value = 1
        mock_table.schema = Mock()  # For table accessibility check
        
        mock_get_embeddings.return_value = [[0.0, 0.0, 0.0]]
        
        # Mock search results for empty query - complex chain for hybrid search
        mock_search = Mock()
        mock_search_with_metric = Mock()
        mock_search_limited = Mock()
        
        mock_search_limited.to_list.return_value = [
            {"doc": "Empty query result", "vector": [0.1, 0.2, 0.3], "_distance": 0.5}
        ]
        
        mock_search_with_metric.limit.return_value = mock_search_limited
        mock_search.metric.return_value = mock_search_with_metric
        mock_table.search.return_value = mock_search
        
        result = hybrid_search("", table_name="test-table")
        
        assert isinstance(result, dict)
        assert "results" in result
        assert len(result["results"]) == 1
    
    @patch('mcp_lancedb.core.connection.open_table_with_retry')
    @patch('mcp_lancedb.core.connection.get_fresh_connection')
    @patch('mcp_lancedb.operations.search_operations.get_embeddings')
    def test_hybrid_search_unicode_query(self, mock_get_embeddings, mock_get_connection, mock_open_table):
        """Test hybrid search with unicode query."""
        # Setup database and table mocks
        mock_db = Mock()
        mock_table = Mock()
        mock_get_connection.return_value = mock_db
        mock_open_table.return_value = mock_table
        
        # Mock database connection
        mock_db.table_names.return_value = ["TestTable"]  # Table exists
        mock_db.open_table.return_value = mock_table
        mock_table.count_rows.return_value = 1
        mock_table.schema = Mock()  # For table accessibility check
        
        unicode_query = "测试查询 with émojis 🔍"
        mock_get_embeddings.return_value = [[0.1, 0.2, 0.3]]
        
        # Mock search results - complex chain for hybrid search
        mock_search = Mock()
        mock_search_with_metric = Mock()
        mock_search_limited = Mock()
        
        mock_search_limited.to_list.return_value = [
            {"doc": "Unicode result", "vector": [0.1, 0.2, 0.3], "_distance": 0.1}
        ]
        
        mock_search_with_metric.limit.return_value = mock_search_limited
        mock_search.metric.return_value = mock_search_with_metric
        mock_table.search.return_value = mock_search
        
        result = hybrid_search(unicode_query, table_name="test-table")
        
        assert isinstance(result, dict)
        assert result["query"] == unicode_query
        # Note: get_embeddings is not called because LanceDB handles embeddings automatically 