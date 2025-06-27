"""Unit tests for search operations."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from mcp_lancedb.operations.search_operations import (
    query_table,
    hybrid_search,
    get_embeddings
)

@pytest.mark.unit
class TestGetEmbeddings:
    """Test the get_embeddings function."""
    
    @patch('mcp_lancedb.core.config.model')
    def test_get_embeddings_success(self, mock_model):
        """Test successful embedding generation."""
        mock_model.embed_documents.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        texts = ["Hello world", "Test document"]
        
        result = get_embeddings(texts)
        
        assert result == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        mock_model.embed_documents.assert_called_once_with(texts)
    
    @patch('mcp_lancedb.core.config.model')
    def test_get_embeddings_error(self, mock_model):
        """Test embedding generation error handling."""
        mock_model.embed_documents.side_effect = Exception("Model error")
        texts = ["Hello world"]
        
        with pytest.raises(Exception):
            get_embeddings(texts)

@pytest.mark.unit
class TestQueryTable:
    """Test the query_table function."""
    
    def make_schema(self, dims=384):
        """Create a mock schema with specified dimensions."""
        mock_field = Mock()
        mock_field.type = f'fixed_size_list<item: float>[{dims}]'
        return [mock_field]

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.get_table_cached')
    @patch('mcp_lancedb.core.connection.verify_table_exists')
    def test_query_table_success(self, mock_verify_exists, mock_get_table, mock_get_connection):
        """Test successful table query."""
        mock_db = Mock()
        mock_table = Mock()
        mock_query = Mock()
        mock_results = Mock()
        
        mock_verify_exists.return_value = True
        mock_get_table.return_value = mock_table
        mock_table.schema = self.make_schema()
        mock_table.count_rows.return_value = 10
        mock_table.search.return_value = mock_query
        mock_query.limit.return_value = mock_results
        mock_results.select.return_value.to_list.return_value = [{"doc": "result", "_distance": 0.1}]
        mock_get_connection.return_value = mock_db
        
        result = query_table("test query", table_name="test-table", top_k=5)
        
        assert isinstance(result, dict)
        assert "results" in result
        assert result["count"] == 1
        assert result["query"] == "test query"
        assert result["table_name"] == "test-table"

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.verify_table_exists')
    def test_query_table_not_exists_no_auto_create(self, mock_verify_exists, mock_get_connection):
        """Test query when table doesn't exist and auto_create is False."""
        mock_verify_exists.return_value = False
        mock_db = Mock()
        mock_get_connection.return_value = mock_db
        
        result = query_table("test query", table_name="nonexistent-table", auto_create_table=False)
        
        assert isinstance(result, str)
        assert "does not exist" in result
        assert "auto_create_table=True" in result

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.verify_table_exists')
    @patch('mcp_lancedb.core.connection.create_table_with_retry')
    def test_query_table_auto_create_success(self, mock_create_table, mock_verify_exists, mock_get_connection):
        """Test auto-creation of table during query."""
        mock_verify_exists.return_value = False
        mock_create_table.return_value = (True, "Success", Mock())
        mock_db = Mock()
        mock_get_connection.return_value = mock_db
        
        result = query_table("test query", table_name="new-table", auto_create_table=True, top_k=0)
        
        assert result is False  # Empty table check returns False
        mock_create_table.assert_called_once()

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.verify_table_exists')
    @patch('mcp_lancedb.core.connection.create_table_with_retry')
    def test_query_table_auto_create_failure(self, mock_create_table, mock_verify_exists, mock_get_connection):
        """Test auto-creation failure during query."""
        mock_verify_exists.return_value = False
        mock_create_table.return_value = (False, "Creation failed", None)
        mock_db = Mock()
        mock_get_connection.return_value = mock_db
        
        result = query_table("test query", table_name="new-table", auto_create_table=True)
        
        assert isinstance(result, str)
        assert "Failed to auto-create table" in result

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.get_table_cached')
    @patch('mcp_lancedb.core.connection.verify_table_exists')
    def test_query_table_empty_table(self, mock_verify_exists, mock_get_table, mock_get_connection):
        """Test query on empty table."""
        mock_db = Mock()
        mock_table = Mock()
        
        mock_verify_exists.return_value = True
        mock_get_table.return_value = mock_table
        mock_table.count_rows.return_value = 0
        mock_get_connection.return_value = mock_db
        
        result = query_table("test query", table_name="empty-table", top_k=5)
        
        assert isinstance(result, dict)
        assert result["results"] == []
        assert result["count"] == 0

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.get_table_cached')
    @patch('mcp_lancedb.core.connection.verify_table_exists')
    def test_query_table_existence_check(self, mock_verify_exists, mock_get_table, mock_get_connection):
        """Test query with top_k=0 for existence check."""
        mock_db = Mock()
        mock_table = Mock()
        mock_query = Mock()
        
        mock_verify_exists.return_value = True
        mock_get_table.return_value = mock_table
        mock_table.schema = self.make_schema()
        mock_table.count_rows.return_value = 5
        mock_table.search.return_value = mock_query
        mock_query.limit.return_value.to_list.return_value = [{"doc": "result"}]
        mock_get_connection.return_value = mock_db
        
        result = query_table("test query", table_name="test-table", top_k=0)
        
        assert result is True  # Found results

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.get_table_cached')
    @patch('mcp_lancedb.core.connection.verify_table_exists')
    def test_query_table_existence_check_no_results(self, mock_verify_exists, mock_get_table, mock_get_connection):
        """Test existence check when no results found."""
        mock_db = Mock()
        mock_table = Mock()
        mock_query = Mock()
        
        mock_verify_exists.return_value = True
        mock_get_table.return_value = mock_table
        mock_table.schema = self.make_schema()
        mock_table.count_rows.return_value = 5
        mock_table.search.return_value = mock_query
        mock_query.limit.return_value.to_list.return_value = []
        mock_get_connection.return_value = mock_db
        
        result = query_table("test query", table_name="test-table", top_k=0)
        
        assert result is False  # No results found

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.get_table_cached')
    @patch('mcp_lancedb.core.connection.verify_table_exists')
    def test_query_table_dimension_mismatch(self, mock_verify_exists, mock_get_table, mock_get_connection):
        """Test query with dimension mismatch between table and model."""
        mock_db = Mock()
        mock_table = Mock()
        
        mock_verify_exists.return_value = True
        mock_get_table.return_value = mock_table
        mock_table.schema = self.make_schema(dims=512)  # Different dimensions
        mock_get_connection.return_value = mock_db
        
        # Mock the model to return different dimensions
        with patch('mcp_lancedb.core.config.model') as mock_model:
            mock_model.ndims.return_value = 384
            
            result = query_table("test query", table_name="test-table")
            
            assert isinstance(result, str)
            assert "dimensional vectors" in result

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.get_table_cached')
    @patch('mcp_lancedb.core.connection.verify_table_exists')
    def test_query_table_search_error_with_retry(self, mock_verify_exists, mock_get_table, mock_get_connection):
        """Test search error with retry mechanism."""
        mock_db = Mock()
        mock_table = Mock()
        mock_query = Mock()
        
        mock_verify_exists.return_value = True
        mock_get_table.return_value = mock_table
        mock_table.schema = self.make_schema()
        mock_table.count_rows.return_value = 5
        mock_table.search.side_effect = [Exception("Search failed"), mock_query]
        mock_query.limit.return_value.select.return_value.to_list.return_value = [{"doc": "result"}]
        mock_get_connection.return_value = mock_db
        
        # Mock get_table_cached to return different table on retry
        mock_get_table.side_effect = [mock_table, mock_table]
        
        result = query_table("test query", table_name="test-table")
        
        assert isinstance(result, dict)
        assert "results" in result

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.get_table_cached')
    @patch('mcp_lancedb.core.connection.verify_table_exists')
    def test_query_table_search_error_no_retry(self, mock_verify_exists, mock_get_table, mock_get_connection):
        """Test search error without successful retry."""
        mock_db = Mock()
        mock_table = Mock()
        
        mock_verify_exists.return_value = True
        mock_get_table.return_value = mock_table
        mock_table.schema = self.make_schema()
        mock_table.count_rows.return_value = 5
        mock_table.search.side_effect = Exception("Search failed")
        mock_get_connection.return_value = mock_db
        
        result = query_table("test query", table_name="test-table")
        
        assert isinstance(result, str)
        assert "Unable to search table" in result

    def test_query_table_invalid_top_k(self):
        """Test query with invalid top_k parameter."""
        result = query_table("test query", top_k=-1)
        
        assert isinstance(result, str)
        assert "top_k must be non-negative" in result

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.get_table_cached')
    @patch('mcp_lancedb.core.connection.verify_table_exists')
    def test_query_table_count_rows_error(self, mock_verify_exists, mock_get_table, mock_get_connection):
        """Test query when count_rows fails."""
        mock_db = Mock()
        mock_table = Mock()
        mock_query = Mock()
        
        mock_verify_exists.return_value = True
        mock_get_table.return_value = mock_table
        mock_table.schema = self.make_schema()
        mock_table.count_rows.side_effect = Exception("Count error")
        mock_table.search.return_value = mock_query
        mock_query.limit.return_value.select.return_value.to_list.return_value = [{"doc": "result"}]
        mock_get_connection.return_value = mock_db
        
        result = query_table("test query", table_name="test-table")
        
        # Should continue despite count error
        assert isinstance(result, dict)
        assert "results" in result

@pytest.mark.unit
class TestHybridSearch:
    """Test the hybrid_search function."""
    
    def make_schema(self, dims=384):
        """Create a mock schema with specified dimensions."""
        mock_field = Mock()
        mock_field.type = f'fixed_size_list<item: float>[{dims}]'
        return [mock_field]

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.get_table_cached')
    @patch('mcp_lancedb.core.connection.verify_table_exists')
    def test_hybrid_search_success(self, mock_verify_exists, mock_get_table, mock_get_connection):
        """Test successful hybrid search."""
        mock_db = Mock()
        mock_table = Mock()
        mock_search = Mock()
        
        mock_verify_exists.return_value = True
        mock_get_table.return_value = mock_table
        mock_table.search.return_value = mock_search
        mock_search.metric.return_value = mock_search
        mock_search.limit.return_value.to_list.return_value = [{"doc": "result", "_distance": 0.1}]
        mock_get_connection.return_value = mock_db
        
        result = hybrid_search("test query", table_name="test-table", top_k=5)
        
        assert isinstance(result, dict)
        assert "results" in result
        assert result["search_type"] == "hybrid"
        assert result["metric"] == "cosine"

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.verify_table_exists')
    def test_hybrid_search_table_not_exists_no_auto_create(self, mock_verify_exists, mock_get_connection):
        """Test hybrid search when table doesn't exist and auto_create is False."""
        mock_verify_exists.return_value = False
        mock_db = Mock()
        mock_get_connection.return_value = mock_db
        
        result = hybrid_search("test query", table_name="nonexistent-table", auto_create_table=False)
        
        assert isinstance(result, str)
        assert "does not exist" in result

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.verify_table_exists')
    @patch('mcp_lancedb.core.connection.create_table_with_retry')
    def test_hybrid_search_auto_create_success(self, mock_create_table, mock_verify_exists, mock_get_connection):
        """Test auto-creation during hybrid search."""
        mock_verify_exists.return_value = False
        mock_create_table.return_value = (True, "Success", Mock())
        mock_db = Mock()
        mock_get_connection.return_value = mock_db
        
        result = hybrid_search("test query", table_name="new-table", auto_create_table=True, top_k=0)
        
        assert result is False  # Empty table check returns False

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.get_table_cached')
    @patch('mcp_lancedb.core.connection.verify_table_exists')
    def test_hybrid_search_with_filter(self, mock_verify_exists, mock_get_table, mock_get_connection):
        """Test hybrid search with filter expression."""
        mock_db = Mock()
        mock_table = Mock()
        mock_search = Mock()
        
        mock_verify_exists.return_value = True
        mock_get_table.return_value = mock_table
        mock_table.search.return_value = mock_search
        mock_search.metric.return_value = mock_search
        mock_search.where.return_value = mock_search
        mock_search.limit.return_value.to_list.return_value = [{"doc": "result", "_distance": 0.1}]
        mock_get_connection.return_value = mock_db
        
        result = hybrid_search("test query", table_name="test-table", filter_expr="category = 'test'")
        
        assert isinstance(result, dict)
        assert "results" in result
        mock_search.where.assert_called_once_with("category = 'test'")

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.get_table_cached')
    @patch('mcp_lancedb.core.connection.verify_table_exists')
    def test_hybrid_search_with_distance_filter(self, mock_verify_exists, mock_get_table, mock_get_connection):
        """Test hybrid search with distance filter in expression."""
        mock_db = Mock()
        mock_table = Mock()
        mock_search = Mock()
        
        mock_verify_exists.return_value = True
        mock_get_table.return_value = mock_table
        mock_table.search.return_value = mock_search
        mock_search.metric.return_value = mock_search
        mock_search.limit.return_value.to_list.return_value = [{"doc": "result", "_distance": 0.1}]
        mock_get_connection.return_value = mock_db
        
        result = hybrid_search("test query", table_name="test-table", filter_expr="_distance <= 0.5")
        
        assert isinstance(result, dict)
        assert "results" in result

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.get_table_cached')
    @patch('mcp_lancedb.core.connection.verify_table_exists')
    def test_hybrid_search_with_distance_threshold(self, mock_verify_exists, mock_get_table, mock_get_connection):
        """Test hybrid search with distance threshold parameter."""
        mock_db = Mock()
        mock_table = Mock()
        mock_search = Mock()
        
        mock_verify_exists.return_value = True
        mock_get_table.return_value = mock_table
        mock_table.search.return_value = mock_search
        mock_search.metric.return_value = mock_search
        mock_search.limit.return_value.to_list.return_value = [
            {"doc": "result1", "_distance": 0.1},
            {"doc": "result2", "_distance": 0.8}
        ]
        mock_get_connection.return_value = mock_db
        
        result = hybrid_search("test query", table_name="test-table", distance_threshold=0.5)
        
        assert isinstance(result, dict)
        assert "results" in result

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.get_table_cached')
    @patch('mcp_lancedb.core.connection.verify_table_exists')
    def test_hybrid_search_different_metrics(self, mock_verify_exists, mock_get_table, mock_get_connection):
        """Test hybrid search with different distance metrics."""
        mock_db = Mock()
        mock_table = Mock()
        mock_search = Mock()
        
        mock_verify_exists.return_value = True
        mock_get_table.return_value = mock_table
        mock_table.search.return_value = mock_search
        mock_search.metric.return_value = mock_search
        mock_search.limit.return_value.to_list.return_value = [{"doc": "result", "_distance": 0.1}]
        mock_get_connection.return_value = mock_db
        
        # Test different metrics
        metrics = ["cosine", "dot", "l2", "euclidean", "hamming"]
        for metric in metrics:
            result = hybrid_search("test query", table_name="test-table", metric=metric)
            assert isinstance(result, dict)
            assert result["metric"] == metric

    def test_hybrid_search_invalid_metric(self):
        """Test hybrid search with invalid distance metric."""
        # Mock the table existence check to pass
        with patch('mcp_lancedb.core.connection.verify_table_exists', return_value=True):
            with patch('mcp_lancedb.core.connection.get_table_cached'):
                result = hybrid_search("test query", metric="invalid_metric")
                
                assert isinstance(result, str)
                assert "Invalid distance metric" in result

    def test_hybrid_search_invalid_top_k(self):
        """Test hybrid search with invalid top_k parameter."""
        result = hybrid_search("test query", top_k=-1)
        
        assert isinstance(result, str)
        assert "top_k must be non-negative" in result

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.get_table_cached')
    @patch('mcp_lancedb.core.connection.verify_table_exists')
    def test_hybrid_search_filter_error(self, mock_verify_exists, mock_get_table, mock_get_connection):
        """Test hybrid search with invalid filter expression."""
        mock_db = Mock()
        mock_table = Mock()
        mock_search = Mock()
        
        mock_verify_exists.return_value = True
        mock_get_table.return_value = mock_table
        mock_table.search.return_value = mock_search
        mock_search.metric.return_value = mock_search
        mock_search.where.side_effect = Exception("Invalid filter")
        mock_get_connection.return_value = mock_db
        
        result = hybrid_search("test query", table_name="test-table", filter_expr="invalid filter")
        
        assert isinstance(result, str)
        assert "Invalid filter expression" in result

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.get_table_cached')
    @patch('mcp_lancedb.core.connection.verify_table_exists')
    def test_hybrid_search_existence_check(self, mock_verify_exists, mock_get_table, mock_get_connection):
        """Test hybrid search with top_k=0 for existence check."""
        mock_db = Mock()
        mock_table = Mock()
        mock_search = Mock()
        
        mock_verify_exists.return_value = True
        mock_get_table.return_value = mock_table
        mock_table.search.return_value = mock_search
        mock_search.metric.return_value = mock_search
        mock_search.limit.return_value.to_list.return_value = [{"doc": "result"}]
        mock_get_connection.return_value = mock_db
        
        result = hybrid_search("test query", table_name="test-table", top_k=0)
        
        assert result is True  # Found results

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.get_table_cached')
    @patch('mcp_lancedb.core.connection.verify_table_exists')
    def test_hybrid_search_search_error(self, mock_verify_exists, mock_get_table, mock_get_connection):
        """Test hybrid search when search execution fails."""
        mock_db = Mock()
        mock_table = Mock()
        mock_search = Mock()
        
        mock_verify_exists.return_value = True
        mock_get_table.return_value = mock_table
        mock_table.search.return_value = mock_search
        mock_search.metric.return_value = mock_search
        mock_search.limit.return_value.to_list.side_effect = Exception("Search failed")
        mock_get_connection.return_value = mock_db
        
        result = hybrid_search("test query", table_name="test-table")
        
        assert isinstance(result, str)
        assert "Search failed" in result 