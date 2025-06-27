"""Unit tests for table management operations."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from mcp_lancedb.operations.table_management import (
    create_table,
    table_details,
    table_stats,
    list_tables,
    table_count,
    delete_table
)

@pytest.mark.unit
class TestCreateTable:
    """Test the create_table function."""
    
    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.create_table_with_retry')
    def test_create_table_success(self, mock_create_table, mock_get_connection):
        """Test successful table creation."""
        mock_db = Mock()
        mock_table = Mock()
        
        mock_create_table.return_value = (True, "Table created successfully", mock_table)
        mock_get_connection.return_value = mock_db
        
        result = create_table("test-table", {"doc": "str", "vector": "Vector(384)"})
        
        assert isinstance(result, str)
        assert "created successfully" in result

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.create_table_with_retry')
    def test_create_table_failure(self, mock_create_table, mock_get_connection):
        """Test table creation failure."""
        mock_db = Mock()
        
        mock_create_table.return_value = (False, "Table already exists", None)
        mock_get_connection.return_value = mock_db
        
        result = create_table("existing-table", {"doc": "str", "vector": "Vector(384)"})
        
        assert isinstance(result, str)
        assert "already exists" in result

    @patch('mcp_lancedb.core.connection.get_connection')
    def test_create_table_connection_error(self, mock_get_connection):
        """Test table creation when connection fails."""
        mock_get_connection.side_effect = Exception("Connection error")
        
        result = create_table("test-table", {"doc": "str", "vector": "Vector(384)"})
        
        assert isinstance(result, str)
        assert "Error creating table" in result

    def test_create_table_invalid_name(self):
        """Test table creation with invalid table name."""
        result = create_table("", {"doc": "str", "vector": "Vector(384)"})
        
        assert isinstance(result, str)
        assert "Error" in result

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.create_table_with_retry')
    def test_create_table_default_schema(self, mock_create_table, mock_get_connection):
        """Test table creation with default schema."""
        mock_db = Mock()
        mock_table = Mock()
        
        mock_create_table.return_value = (True, "Table created successfully", mock_table)
        mock_get_connection.return_value = mock_db
        
        result = create_table("test-table")
        
        assert isinstance(result, str)
        assert "created successfully" in result
        # Should use default schema with doc and vector fields
        mock_create_table.assert_called_once()

@pytest.mark.unit
class TestTableDetails:
    """Test the table_details function."""
    
    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.get_table_cached')
    @patch('mcp_lancedb.core.connection.verify_table_exists')
    def test_table_details_success(self, mock_verify_exists, mock_get_table, mock_get_connection):
        """Test successful table details retrieval."""
        mock_db = Mock()
        mock_table = Mock()
        
        mock_verify_exists.return_value = True
        mock_get_table.return_value = mock_table
        mock_table.schema = [Mock(), Mock()]
        mock_table.count_rows.return_value = 100
        mock_get_connection.return_value = mock_db
        
        result = table_details("test-table")
        
        assert isinstance(result, dict)
        assert "name" in result
        assert "schema" in result
        assert "row_count" in result
        assert result["name"] == "test-table"

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.verify_table_exists')
    def test_table_details_not_exists(self, mock_verify_exists, mock_get_connection):
        """Test table details when table doesn't exist."""
        mock_db = Mock()
        
        mock_verify_exists.return_value = False
        mock_get_connection.return_value = mock_db
        
        result = table_details("nonexistent-table")
        
        assert isinstance(result, str)
        assert "does not exist" in result

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.get_table_cached')
    @patch('mcp_lancedb.core.connection.verify_table_exists')
    def test_table_details_error(self, mock_verify_exists, mock_get_table, mock_get_connection):
        """Test table details when error occurs."""
        mock_db = Mock()
        mock_table = Mock()
        
        mock_verify_exists.return_value = True
        mock_get_table.return_value = mock_table
        mock_table.schema = [Mock(), Mock()]
        mock_table.count_rows.side_effect = Exception("Count error")
        mock_get_connection.return_value = mock_db
        
        result = table_details("test-table")
        
        assert isinstance(result, str)
        assert "Error getting table details" in result

@pytest.mark.unit
class TestTableStats:
    """Test the table_stats function."""
    
    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.get_table_cached')
    @patch('mcp_lancedb.core.connection.verify_table_exists')
    def test_table_stats_success(self, mock_verify_exists, mock_get_table, mock_get_connection):
        """Test successful table stats retrieval."""
        mock_db = Mock()
        mock_table = Mock()
        
        mock_verify_exists.return_value = True
        mock_get_table.return_value = mock_table
        mock_table.schema = [Mock(), Mock()]
        mock_table.count_rows.return_value = 100
        mock_get_connection.return_value = mock_db
        
        result = table_stats("test-table")
        
        assert isinstance(result, dict)
        assert "name" in result
        assert "row_count" in result
        assert "schema_info" in result
        assert "field_categories" in result

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.verify_table_exists')
    def test_table_stats_not_exists(self, mock_verify_exists, mock_get_connection):
        """Test table stats when table doesn't exist."""
        mock_db = Mock()
        
        mock_verify_exists.return_value = False
        mock_get_connection.return_value = mock_db
        
        result = table_stats("nonexistent-table")
        
        assert isinstance(result, str)
        assert "does not exist" in result

@pytest.mark.unit
class TestListTables:
    """Test the list_tables function."""
    
    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.get_all_tables')
    def test_list_tables_success(self, mock_get_all_tables, mock_get_connection):
        """Test successful table listing."""
        mock_db = Mock()
        mock_table1 = Mock()
        mock_table2 = Mock()
        
        # Configure mock tables
        mock_table1.name = "test-table-1"
        mock_table2.name = "test-table-2"
        
        mock_get_all_tables.return_value = [mock_table1, mock_table2]
        mock_get_connection.return_value = mock_db
        
        result = list_tables()
        
        assert isinstance(result, dict)
        assert "tables" in result
        assert len(result["tables"]) == 2
        assert "test-table-1" in result["tables"]
        assert "test-table-2" in result["tables"]

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.get_all_tables')
    def test_list_tables_empty(self, mock_get_all_tables, mock_get_connection):
        """Test table listing when no tables exist."""
        mock_db = Mock()
        mock_get_all_tables.return_value = []
        mock_get_connection.return_value = mock_db
        
        result = list_tables()
        
        assert isinstance(result, dict)
        assert "tables" in result
        assert result["tables"] == []

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.get_all_tables')
    def test_list_tables_error(self, mock_get_all_tables, mock_get_connection):
        """Test table listing when database error occurs."""
        mock_db = Mock()
        mock_get_all_tables.side_effect = Exception("Database error")
        mock_get_connection.return_value = mock_db
        
        result = list_tables()
        
        assert isinstance(result, str)
        assert "Error listing tables" in result

@pytest.mark.unit
class TestTableCount:
    """Test the table_count function."""
    
    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.get_all_tables')
    def test_table_count_success(self, mock_get_all_tables, mock_get_connection):
        """Test successful table counting."""
        mock_db = Mock()
        mock_table1 = Mock()
        mock_table2 = Mock()
        mock_table3 = Mock()
        
        mock_get_all_tables.return_value = [mock_table1, mock_table2, mock_table3]
        mock_get_connection.return_value = mock_db
        
        result = table_count()
        
        assert isinstance(result, dict)
        assert "count" in result
        assert result["count"] == 3

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.get_all_tables')
    def test_table_count_empty(self, mock_get_all_tables, mock_get_connection):
        """Test table counting when no tables exist."""
        mock_db = Mock()
        mock_get_all_tables.return_value = []
        mock_get_connection.return_value = mock_db
        
        result = table_count()
        
        assert isinstance(result, dict)
        assert "count" in result
        assert result["count"] == 0

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.get_all_tables')
    def test_table_count_error(self, mock_get_all_tables, mock_get_connection):
        """Test table counting when database error occurs."""
        mock_db = Mock()
        mock_get_all_tables.side_effect = Exception("Database error")
        mock_get_connection.return_value = mock_db
        
        result = table_count()
        
        assert isinstance(result, str)
        assert "Error counting tables" in result

@pytest.mark.unit
class TestDeleteTable:
    """Test the delete_table function."""
    
    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.verify_table_exists')
    def test_delete_table_success(self, mock_verify_exists, mock_get_connection):
        """Test successful table deletion."""
        mock_db = Mock()
        
        mock_verify_exists.return_value = True
        mock_db.drop_table.return_value = None
        mock_get_connection.return_value = mock_db
        
        result = delete_table("test-table")
        
        assert isinstance(result, str)
        assert "deleted successfully" in result
        mock_db.drop_table.assert_called_once_with("test-table")

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.verify_table_exists')
    def test_delete_table_not_exists(self, mock_verify_exists, mock_get_connection):
        """Test deletion of non-existent table."""
        mock_db = Mock()
        
        mock_verify_exists.return_value = False
        mock_get_connection.return_value = mock_db
        
        result = delete_table("nonexistent-table")
        
        assert isinstance(result, str)
        assert "does not exist" in result

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.verify_table_exists')
    def test_delete_table_error(self, mock_verify_exists, mock_get_connection):
        """Test table deletion when error occurs."""
        mock_db = Mock()
        
        mock_verify_exists.return_value = True
        mock_db.drop_table.side_effect = Exception("Delete error")
        mock_get_connection.return_value = mock_db
        
        result = delete_table("test-table")
        
        assert isinstance(result, str)
        assert "Error deleting table" in result

    def test_delete_table_invalid_name(self):
        """Test table deletion with invalid table name."""
        result = delete_table("")
        
        assert isinstance(result, str)
        assert "Error" in result 