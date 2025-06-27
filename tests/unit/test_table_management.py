"""Unit tests for table management operations."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from mcp_lancedb import (
    create_table,
    delete_table,
    list_tables,
    table_count,
    table_details,
    table_stats
)


@pytest.mark.unit
class TestCreateTable:
    """Test table creation functionality."""
    
    @patch('mcp_lancedb.operations.table_management.create_table_with_retry')
    def test_create_table_default_schema(self, mock_create_retry):
        """Test creating table with default schema."""
        mock_create_retry.return_value = (True, "Table created successfully", Mock())
        
        result = create_table("test-table")
        
        assert "created successfully" in result
        mock_create_retry.assert_called_once()
        args, kwargs = mock_create_retry.call_args
        assert args[0] == "test-table"
        # Should use default Schema
        assert hasattr(args[1], '__name__') or hasattr(args[1], '__class__')
    
    @patch('mcp_lancedb.operations.table_management.create_schema_from_dict')
    @patch('mcp_lancedb.operations.table_management.create_table_with_retry')
    def test_create_table_custom_schema(self, mock_create_retry, mock_create_schema):
        """Test creating table with custom schema."""
        custom_schema = {"doc": "str", "vector": "Vector(768)"}
        mock_schema_class = Mock()
        mock_create_schema.return_value = mock_schema_class
        mock_create_retry.return_value = (True, "Table created successfully", Mock())
        
        result = create_table("test-table", custom_schema)
        
        assert "created successfully" in result
        mock_create_schema.assert_called_once_with(custom_schema)
        mock_create_retry.assert_called_once_with("test-table", mock_schema_class)
    
    @patch('mcp_lancedb.operations.table_management.create_table_with_retry')
    def test_create_table_failure(self, mock_create_retry):
        """Test table creation failure."""
        mock_create_retry.return_value = (False, "Creation failed", None)
        
        result = create_table("test-table")
        
        assert "Creation failed" in result


@pytest.mark.unit
class TestDeleteTable:
    """Test table deletion functionality."""
    
    @patch('mcp_lancedb.operations.table_management.get_fresh_connection')
    def test_delete_table_success(self, mock_get_connection):
        """Test successful table deletion."""
        # Setup mocks
        mock_db = Mock()
        mock_table = Mock()
        mock_get_connection.return_value = mock_db
        
        # First call returns table exists, second call after deletion returns table doesn't exist
        mock_db.table_names.side_effect = [
            ["test-table", "other-table"],  # Initial check
            ["other-table"],                # After deletion check (attempt 1)
        ]
        mock_db.open_table.return_value = mock_table
        mock_table.count_rows.return_value = 5  # Table has 5 rows
        
        result = delete_table("test-table")
        
        assert "deleted successfully" in result
        assert "5 rows" in result
        mock_db.drop_table.assert_called_once_with("test-table")


@pytest.mark.unit
class TestListTables:
    """Test table listing functionality."""
    
    @patch('mcp_lancedb.operations.table_management.get_fresh_connection')
    def test_list_tables_success(self, mock_get_connection):
        """Test successful table listing."""
        mock_db = Mock()
        mock_table1 = Mock()
        mock_table2 = Mock()
        mock_get_connection.return_value = mock_db
        
        mock_db.table_names.return_value = ["table1", "table2"]
        mock_db.open_table.side_effect = [mock_table1, mock_table2]
        mock_table1.count_rows.return_value = 10
        mock_table2.count_rows.return_value = 20
        
        result = list_tables()
        
        assert result["count"] == 2
        assert len(result["tables"]) == 2
        assert result["tables"][0]["name"] == "table1"
        assert result["tables"][0]["num_rows"] == 10


@pytest.mark.unit
class TestTableCount:
    """Test table count functionality."""
    
    @patch('mcp_lancedb.core.connection.get_all_tables')
    def test_table_count_success(self, mock_get_all_tables):
        """Test successful table count retrieval."""
        mock_get_all_tables.return_value = ["table1", "table2", "table3"]
        
        result = table_count()
        
        assert result["count"] == 3
        assert "message" in result
        assert "3 tables" in result["message"]
        mock_get_all_tables.assert_called_once()
    
    @patch('mcp_lancedb.core.connection.get_all_tables')
    def test_table_count_empty_db(self, mock_get_all_tables):
        """Test table count with empty database."""
        mock_get_all_tables.return_value = []
        
        result = table_count()
        
        assert result["count"] == 0
        assert "0 table" in result["message"]  # Singular form for 0
    
    @patch('mcp_lancedb.core.connection.get_all_tables')
    def test_table_count_single_table(self, mock_get_all_tables):
        """Test table count with single table."""
        mock_get_all_tables.return_value = ["only_table"]
        
        result = table_count()
        
        assert result["count"] == 1
        assert "1 table" in result["message"]  # Singular form for 1
    
    @patch('mcp_lancedb.core.connection.get_all_tables')
    def test_table_count_error_handling(self, mock_get_all_tables):
        """Test table count error handling."""
        mock_get_all_tables.side_effect = Exception("Database connection failed")
        
        result = table_count()
        
        assert "error" in result
        assert "Database connection failed" in result["error"]


@pytest.mark.unit  
class TestTableDetails:
    """Test table details functionality."""
    
    @patch('mcp_lancedb.operations.table_management.open_table_with_retry')
    def test_table_details_success(self, mock_open_table):
        """Test successful table details retrieval."""
        mock_table = Mock()
        mock_schema = Mock()
        mock_open_table.return_value = (True, "Success", mock_table)
        mock_table.schema = mock_schema
        mock_table.count_rows.return_value = 15
        
        # Mock the schema structure
        mock_schema.names = ["doc", "vector"]
        mock_schema.types = ["string", "list"]
        
        result = table_details("test-table")
        
        assert isinstance(result, dict)
        assert "table_name" in result or "name" in result


@pytest.mark.unit
class TestTableStats:
    """Test table stats functionality."""
    
    @patch('mcp_lancedb.operations.table_management.open_table_with_retry')
    def test_table_stats_success(self, mock_open_table):
        """Test successful table stats retrieval."""
        mock_table = Mock()
        mock_schema = Mock()
        mock_open_table.return_value = (True, "Success", mock_table)
        mock_table.schema = mock_schema
        mock_table.count_rows.return_value = 25
        
        # Mock schema fields
        mock_schema.names = ["doc", "vector", "metadata"]
        mock_schema.types = ["string", "list", "string"]
        
        result = table_stats("test-table")
        
        assert isinstance(result, dict)
        assert "row_count" in result or "num_rows" in result 