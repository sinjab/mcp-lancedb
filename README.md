# MCP LanceDB

A production-ready Python package that provides a serverless MCP (Model Context Protocol) server implementation for LanceDB integration with Claude. It enables efficient storage and retrieval of vector embeddings for documents using LanceDB's vector database capabilities.

## Features

- **Table Management** - Create, manage, and delete tables with custom schemas and vector dimensions
- **Document Management** - Automatic document ingestion with vector embeddings, updates, and deletions
- **Search Operations** - Vector similarity search and hybrid search with multiple distance metrics
- **Batch Processing** - Efficient bulk operations for large datasets
- **Multi-language Support** - Unicode, emoji, and special character handling
- **Modular Architecture** - Clean separation of concerns across specialized modules
- **Serverless Design** - Stdio-based communication for Claude integration

## Installation

### Quick Installation

1. **Clone the repository**:
```bash
git clone https://github.com/sinjab/mcp_lancedb.git
cd mcp_lancedb
```

2. **Install dependencies**:
```bash
# With uv (recommended)
uv sync

# Or with pip
pip install -e ".[dev]"
```

3. **Configure Claude MCP**:
Add to your Claude MCP configuration:
```json
{
  "mcpServers": {
    "mcp_lancedb": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/mcp_lancedb",
        "run",
        "mcp-lancedb"
      ]
    }
  }
}
```

### Verify Installation
```bash
# Test the CLI
mcp-lancedb --help

# Run test suite
python run_tests.py all
```

## Configuration

Configure the server using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `LANCEDB_URI` | Database location | `~/lancedb` |
| `TABLE_NAME` | Default table name | `lancedb-mcp-table` |
| `EMBEDDING_FUNCTION` | Embedding model type | `sentence-transformers` |
| `MODEL_NAME` | Specific model to use | `all-MiniLM-L6-v2` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Usage

### Table Management

```python
from mcp_lancedb import create_table, list_tables, table_count, table_details, table_stats, delete_table

# Create a new table (dimensions determined automatically by embedding model)
create_table("my_table")

# Create table with custom schema (dimensions still automatic)
create_table(
    table_name="custom_table",
    schema={
        "doc": "str",
        "vector": "Vector(384)",  # Must match embedding model dimensions
        "metadata": "str", 
        "score": "float"
    }
)

# List all tables with details
all_tables = list_tables()  # Returns table list with row counts

# Get just the table count (lightweight)
count_info = table_count()  # Returns {"count": N, "message": "..."}

# Get detailed table information
stats = table_stats("my_table")
details = table_details("my_table")

# Delete a table
delete_table("my_table")
```

### Document Management

```python
from mcp_lancedb import ingest_docs, update_documents, delete_documents

# Ingest documents
ingest_docs(None, "Hello world")  # Use default table
ingest_docs("my_table", [
    "First document content",
    "Second document content",
    "Third document content"
])

# Update documents
update_documents(
    table_name="my_table",
    filter_expr="metadata == 'draft'",
    updates={"metadata": "published"}
)

# Delete documents
delete_documents(
    table_name="my_table",
    filter_expr="score < 0.1"
)
```

### Search Operations

```python
from mcp_lancedb import query_table, hybrid_search

# Basic vector search
results = query_table(
    query="Your search query",
    top_k=5,
    query_type="vector"
)

# Hybrid search with filtering
results = hybrid_search(
    query="Your search query",
    filter_expr="score > 0.5",
    top_k=5,
    metric="cosine"
)
```

## Architecture

The project follows a clean, modular architecture with organized subfolders:

```
src/mcp_lancedb/
├── server.py              # Main MCP server entry point
├── cli.py                 # Command-line interface
├── __init__.py           # Public API exports
├── core/                  # Core infrastructure
│   ├── config.py         #   Configuration management
│   ├── logger.py         #   Logging infrastructure  
│   ├── connection.py     #   Database connection management
│   └── schemas.py        #   Data schema definitions
└── operations/            # Business logic modules
    ├── table_management.py    #   Table CRUD operations
    ├── document_management.py #   Document ingestion and updates
    └── search_operations.py   #   Vector and hybrid search
```

### Design Principles

- **Clean separation**: Core infrastructure vs. business operations
- **Modular imports**: Import from main module (`from mcp_lancedb import ...`)
- **Organized structure**: Related functionality grouped in logical folders
- **Minimal root**: Only essential files at package root level

## Testing

```bash
# Run all tests
python run_tests.py all

# Run unit tests only
python run_tests.py unit

# Run integration tests
python run_tests.py integration

# Run with coverage
python run_tests.py all --coverage
```

## Best Practices

### Recommended Patterns
```python
# ✅ Use custom schemas for multi-table applications
create_table(
    table_name="reliable_table", 
    schema={
        "doc": "str",
        "vector": "Vector(384)",  # Automatic embedding model dimensions
        "type": "str"
    }
)

# ✅ Single default table usage
ingest_docs(None, ["My document"], auto_create_table=True)
```

### Avoid These Patterns
```python
# ❌ Multiple default schema tables may have persistence issues
create_table("table1")
create_table("table2")

# ❌ Default tables without auto-creation
ingest_docs("default_table", ["Doc"], auto_create_table=False)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure all tests pass: `python run_tests.py all`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [LanceDB](https://lancedb.github.io/lancedb/) for the vector database
- [MCP](https://github.com/modelcontextprotocol/python-sdk) for the Model Context Protocol
- [sentence-transformers](https://www.sbert.net/) for embedding models
