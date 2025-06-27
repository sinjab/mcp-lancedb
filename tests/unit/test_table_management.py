"""Unit tests for table management operations."""

import pytest
from unittest.mock import Mock, patch
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
    @patch('mcp_lancedb.core.connection.sanitize_table_name')
    def test_create_table_success(self, mock_sanitize, mock_get_connection):
        """Test successful table creation."""
        mock_db = Mock()
        mock_table = Mock()
        
        mock_sanitize.return_value = "TestTable"
        mock_db.table_names.return_value = []
        mock_db.create_table.return_value = mock_table
        mock_get_connection.return_value = mock_db
        
        result = create_table("test-table")
        
        assert isinstance(result, str)
        assert "created successfully" in result
        mock_db.create_table.assert_called_once()

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.sanitize_table_name')
    def test_create_table_failure(self, mock_sanitize, mock_get_connection):
        """Test table creation failure."""
        mock_db = Mock()
        
        mock_sanitize.return_value = "TestTable"
        mock_db.table_names.return_value = []
        mock_db.create_table.side_effect = Exception("creation failed")
        mock_get_connection.return_value = mock_db
        
        with pytest.raises(Exception):
            create_table("test-table")

    def test_create_table_invalid_name(self):
        """Test table creation with invalid name."""
        result = create_table("")
        
        assert isinstance(result, str)
        assert "Invalid table name" in result

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.sanitize_table_name')
    def test_create_table_default_schema(self, mock_sanitize, mock_get_connection):
        """Test table creation with default schema."""
        mock_db = Mock()
        mock_table = Mock()
        
        mock_sanitize.return_value = "TestTable"
        mock_db.table_names.return_value = []
        mock_db.create_table.return_value = mock_table
        mock_get_connection.return_value = mock_db
        
        result = create_table("test-table")
        
        assert isinstance(result, str)
        assert "created successfully" in result

@pytest.mark.unit
class TestTableDetails:
    """Test the table_details function."""
    
    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.sanitize_table_name')
    def test_table_details_success(self, mock_sanitize, mock_get_connection):
        """Test successful table details retrieval."""
        mock_db = Mock()
        mock_table = Mock()
        
        mock_sanitize.return_value = "TestTable"
        mock_db.table_names.return_value = ["TestTable"]
        mock_db.open_table.return_value = mock_table
        mock_table.count_rows.return_value = 100
        mock_table.schema = [Mock(type="string"), Mock(type="fixed_size_list<item: float>[384]")]
        mock_get_connection.return_value = mock_db
        
        result = table_details("test-table")
        
        assert isinstance(result, dict)
        assert "name" in result
        assert "row_count" in result
        assert "schema" in result

    @patch('mcp_lancedb.core.connection.sanitize_table_name', return_value="TestTable")
    @patch('mcp_lancedb.core.connection.get_connection')
    def test_table_details_not_exists(self, mock_get_connection, mock_sanitize):
        """Test table details when table doesn't exist."""
        tables = set()
        mock_db = Mock()
        mock_get_connection.return_value = mock_db
        def open_table(name):
            raise Exception("not found")
        def table_names():
            return list(tables)
        mock_db.open_table.side_effect = open_table
        mock_db.table_names.side_effect = table_names
        result = table_details("nonexistent-table")
        assert isinstance(result, str)
        assert "does not exist" in result or "not found" in result

    @patch('mcp_lancedb.core.connection.sanitize_table_name', return_value="TestTable")
    @patch('mcp_lancedb.core.connection.get_connection')
    def test_table_details_error(self, mock_get_connection, mock_sanitize):
        """Test table details when error occurs."""
        tables = {"TestTable"}
        mock_db = Mock()
        mock_get_connection.return_value = mock_db
        def open_table(name):
            raise Exception("some error")
        def table_names():
            return list(tables)
        mock_db.open_table.side_effect = open_table
        mock_db.table_names.side_effect = table_names
        result = table_details("test-table")
        assert isinstance(result, str)
        assert "Error getting table details" in result or "does not exist" in result

@pytest.mark.unit
class TestTableStats:
    """Test the table_stats function."""
    
    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.sanitize_table_name')
    def test_table_stats_success(self, mock_sanitize, mock_get_connection):
        """Test successful table statistics retrieval."""
        mock_db = Mock()
        mock_table = Mock()
        
        mock_sanitize.return_value = "TestTable"
        mock_db.table_names.return_value = ["TestTable"]
        mock_db.open_table.return_value = mock_table
        mock_table.count_rows.return_value = 100
        mock_table.schema = [Mock(type="string"), Mock(type="fixed_size_list<item: float>[384]")]
        mock_get_connection.return_value = mock_db
        
        result = table_stats("test-table")
        
        assert isinstance(result, dict)
        assert "name" in result
        assert "row_count" in result
        assert "schema" in result

    @patch('mcp_lancedb.core.connection.sanitize_table_name', return_value="TestTable")
    @patch('mcp_lancedb.core.connection.get_connection')
    def test_table_stats_not_exists(self, mock_get_connection, mock_sanitize):
        """Test table stats when table doesn't exist."""
        tables = set()
        mock_db = Mock()
        mock_get_connection.return_value = mock_db
        def open_table(name):
            raise Exception("not found")
        def table_names():
            return list(tables)
        mock_db.open_table.side_effect = open_table
        mock_db.table_names.side_effect = table_names
        result = table_stats("nonexistent-table")
        assert isinstance(result, str)
        assert "does not exist" in result or "not found" in result

    @patch('mcp_lancedb.core.connection.sanitize_table_name', return_value="TestTable")
    @patch('mcp_lancedb.core.connection.get_connection')
    def test_table_stats_error(self, mock_get_connection, mock_sanitize):
        """Test table stats when error occurs."""
        tables = {"TestTable"}
        mock_db = Mock()
        mock_get_connection.return_value = mock_db
        def open_table(name):
            raise Exception("some error")
        def table_names():
            return list(tables)
        mock_db.open_table.side_effect = open_table
        mock_db.table_names.side_effect = table_names
        result = table_stats("test-table")
        assert isinstance(result, str)
        assert "Error getting table statistics" in result or "does not exist" in result

@pytest.mark.unit
class TestListTables:
    """Test the list_tables function."""
    
    @patch('mcp_lancedb.core.connection.get_connection')
    def test_list_tables_success(self, mock_get_connection):
        """Test successful table listing."""
        mock_db = Mock()
        mock_db.table_names.return_value = ["test-table-1", "test-table-2"]
        mock_get_connection.return_value = mock_db
        
        result = list_tables()
        
        assert isinstance(result, dict)
        assert "tables" in result
        table_names = result["tables"]
        assert "test-table-1" in table_names
        assert "test-table-2" in table_names

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
        
        assert isinstance(result, dict)
        assert "error" in result
        assert "Error listing tables" in result["error"]

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
        
        assert isinstance(result, dict)
        assert "error" in result
        assert "Error getting table count" in result["error"]

@pytest.mark.unit
class TestDeleteTable:
    """Test the delete_table function."""
    
    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.sanitize_table_name')
    def test_delete_table_success(self, mock_sanitize, mock_get_connection):
        """Test successful table deletion."""
        mock_db = Mock()
        
        mock_sanitize.return_value = "TestTable"
        mock_db.table_names.return_value = ["TestTable"]
        mock_db.drop_table.return_value = None
        mock_get_connection.return_value = mock_db
        
        result = delete_table("test-table")
        
        assert isinstance(result, str)
        assert "deleted successfully" in result
        mock_db.drop_table.assert_called_once_with("TestTable")

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.sanitize_table_name')
    def test_delete_table_error(self, mock_sanitize, mock_get_connection):
        """Test table deletion error."""
        mock_db = Mock()
        
        mock_sanitize.return_value = "TestTable"
        mock_db.table_names.return_value = ["TestTable"]
        mock_db.drop_table.side_effect = Exception("deletion failed")
        mock_get_connection.return_value = mock_db
        
        result = delete_table("test-table")
        
        assert isinstance(result, str)
        assert "Error deleting table" in result

    @patch('mcp_lancedb.core.connection.get_connection')
    @patch('mcp_lancedb.core.connection.sanitize_table_name')
    def test_delete_table_invalid_name(self, mock_sanitize, mock_get_connection):
        """Test table deletion with invalid name."""
        mock_db = Mock()
        
        mock_sanitize.return_value = "DefaultTable"
        mock_db.table_names.return_value = ["DefaultTable"]
        mock_db.drop_table.return_value = None
        mock_get_connection.return_value = mock_db
        
        result = delete_table("")
        
        assert isinstance(result, str)
        assert "deleted successfully" in result 