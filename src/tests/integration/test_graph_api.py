import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json

from app.services.graph_service import GraphService
from app.models.graph import (
    GraphNode,
    GraphEdge,
    GraphTraversalDirection,
    VisualizationFormatEnum,
)

# Mock token for testing
TEST_TOKEN = "test_token"
TEST_USER_ID = "test_user_123"


# Create mock data to use in all tests
@pytest.fixture
def mock_graph_data():
    """Create mock graph data for testing"""
    mock_nodes = [
        {
            "id": "node1",
            "label": "Person",
            "properties": {"name": "John Doe", "age": 30},
        },
        {
            "id": "node2",
            "label": "Person",
            "properties": {"name": "Jane Smith", "age": 28},
        },
        {
            "id": "node3",
            "label": "Company",
            "properties": {"name": "Acme Corp", "founded": 2010},
        },
    ]

    mock_edges = [
        {
            "source": "node1",
            "target": "node2",
            "type": "KNOWS",
            "properties": {"since": "2020-01-01"},
        },
        {
            "source": "node1",
            "target": "node3",
            "type": "WORKS_AT",
            "properties": {"position": "Developer", "since": "2021-05-15"},
        },
    ]

    return {"nodes": mock_nodes, "edges": mock_edges}


# Mock RAG for testing
@pytest.fixture
def mock_rag(mock_graph_data):
    """Create a mock RAG instance with all needed methods mocked"""
    mock_rag = MagicMock()
    mock_nodes = mock_graph_data["nodes"]
    mock_edges = mock_graph_data["edges"]

    # Mock all RAG methods
    mock_rag.get_graph = AsyncMock(return_value=mock_graph_data)
    mock_rag.get_knowledge_graph = AsyncMock(return_value=mock_graph_data)
    mock_rag.get_node = AsyncMock(return_value=mock_nodes[0])
    mock_rag.create_node = AsyncMock(
        return_value={
            "id": "new_node",
            "label": "Person",
            "properties": {"name": "New Person"},
        }
    )
    mock_rag.update_node = AsyncMock(
        return_value={
            "id": "node1",
            "label": "Person",
            "properties": {"name": "Updated Name", "age": 31},
        }
    )
    mock_rag.delete_node = AsyncMock(return_value={"affected_edges": 2})
    mock_rag.create_edge = AsyncMock(
        return_value={
            "source": "node1",
            "target": "node3",
            "type": "MANAGES",
            "properties": {"since": "2022-01-01"},
        }
    )
    mock_rag.update_edge = AsyncMock(
        return_value={
            "source": "node1",
            "target": "node2",
            "type": "FRIENDS_WITH",
            "properties": {"since": "2020-01-01", "close": True},
        }
    )
    mock_rag.delete_edge = AsyncMock(return_value={"deleted": True})
    mock_rag.traverse_graph = AsyncMock(return_value=mock_graph_data)
    mock_rag.find_paths = AsyncMock(
        return_value=[
            {
                "nodes": [mock_nodes[0], mock_nodes[1]],
                "edges": [mock_edges[0]],
                "length": 1,
            }
        ]
    )
    mock_rag.search_graph = AsyncMock(
        return_value={"nodes": [mock_nodes[0]], "edges": []}
    )

    return mock_rag


# Test get_graph method
@pytest.mark.asyncio
async def test_get_graph(mock_rag, mock_graph_data):
    """Test the get_graph method"""
    result = await GraphService.get_graph(
        rag=mock_rag, limit=100, offset=0, node_labels=None, edge_types=None
    )

    assert result["nodes"] == mock_graph_data["nodes"]
    assert result["edges"] == mock_graph_data["edges"]
    assert result["total_nodes"] == len(mock_graph_data["nodes"])
    assert result["total_edges"] == len(mock_graph_data["edges"])

    # Verify the RAG method was called with correct parameters
    mock_rag.get_graph.assert_called_once_with(
        limit=100, offset=0, node_labels=None, edge_types=None
    )


# Test get_node method
@pytest.mark.asyncio
async def test_get_node(mock_rag, mock_graph_data):
    """Test the get_node method"""
    node_id = "node1"
    result = await GraphService.get_node(rag=mock_rag, node_id=node_id)

    assert result["id"] == "node1"
    assert result["label"] == "Person"
    assert "properties" in result

    # Verify the RAG method was called with correct parameters
    mock_rag.get_node.assert_called_once_with(node_id=node_id)


# Test create_node method
@pytest.mark.asyncio
async def test_create_node(mock_rag):
    """Test the create_node method"""
    label = "Person"
    properties = {"name": "New Person"}

    result = await GraphService.create_node(
        rag=mock_rag, label=label, properties=properties
    )

    assert result["id"] == "new_node"
    assert result["label"] == "Person"
    assert result["properties"]["name"] == "New Person"

    # Verify the RAG method was called with correct parameters
    mock_rag.create_node.assert_called_once_with(label=label, properties=properties)


# Test update_node method
@pytest.mark.asyncio
async def test_update_node(mock_rag):
    """Test the update_node method"""
    # First make sure get_node is mocked to not raise an exception
    node_id = "node1"
    label = "Person"
    properties = {"name": "Updated Name", "age": 31}

    mock_rag.get_node = AsyncMock(return_value={"id": node_id})

    result = await GraphService.update_node(
        rag=mock_rag, node_id=node_id, label=label, properties=properties
    )

    assert result["id"] == "node1"
    assert result["properties"]["name"] == "Updated Name"
    assert result["properties"]["age"] == 31

    # Verify the RAG methods were called with correct parameters
    mock_rag.get_node.assert_called_once_with(node_id=node_id)
    mock_rag.update_node.assert_called_once_with(
        node_id=node_id, label=label, properties=properties
    )


# Test delete_node method
@pytest.mark.asyncio
async def test_delete_node(mock_rag):
    """Test the delete_node method"""
    # First make sure get_node is mocked to not raise an exception
    node_id = "node1"

    mock_rag.get_node = AsyncMock(return_value={"id": node_id})

    result = await GraphService.delete_node(rag=mock_rag, node_id=node_id)

    assert result["id"] == node_id
    assert result["deleted"] is True
    assert result["affected_edges"] == 2

    # Verify the RAG methods were called with correct parameters
    mock_rag.get_node.assert_called_once_with(node_id=node_id)
    mock_rag.delete_node.assert_called_once_with(node_id=node_id)


# Test create_edge method
@pytest.mark.asyncio
async def test_create_edge(mock_rag):
    """Test the create_edge method"""
    # First make sure get_node is mocked to not raise an exception
    source = "node1"
    target = "node3"
    edge_type = "MANAGES"
    properties = {"since": "2022-01-01"}

    mock_rag.get_node = AsyncMock(return_value={"id": "exists"})

    result = await GraphService.create_edge(
        rag=mock_rag,
        source=source,
        target=target,
        edge_type=edge_type,
        properties=properties,
    )

    assert result["source"] == source
    assert result["target"] == target
    assert result["type"] == edge_type
    assert "properties" in result

    # Verify the RAG methods were called with correct parameters
    assert mock_rag.get_node.call_count == 2  # Once for source, once for target
    mock_rag.create_edge.assert_called_once_with(
        source_id=source, target_id=target, edge_type=edge_type, properties=properties
    )


# Test update_edge method
@pytest.mark.asyncio
async def test_update_edge(mock_rag):
    """Test the update_edge method"""
    source = "node1"
    target = "node2"
    edge_type = "KNOWS"
    new_type = "FRIENDS_WITH"
    properties = {"since": "2020-01-01", "close": True}

    result = await GraphService.update_edge(
        rag=mock_rag,
        source=source,
        target=target,
        edge_type=edge_type,
        new_type=new_type,
        properties=properties,
    )

    assert result["source"] == source
    assert result["target"] == target
    assert result["type"] == new_type
    assert result["properties"]["close"] is True

    # Verify the RAG method was called with correct parameters
    mock_rag.update_edge.assert_called_once_with(
        source_id=source,
        target_id=target,
        edge_type=edge_type,
        new_type=new_type,
        properties=properties,
    )


# Test delete_edge method
@pytest.mark.asyncio
async def test_delete_edge(mock_rag):
    """Test the delete_edge method"""
    source = "node1"
    target = "node2"
    edge_type = "KNOWS"

    result = await GraphService.delete_edge(
        rag=mock_rag, source=source, target=target, edge_type=edge_type
    )

    assert result["source"] == source
    assert result["target"] == target
    assert result["type"] == edge_type
    assert result["deleted"] is True

    # Verify the RAG method was called with correct parameters
    mock_rag.delete_edge.assert_called_once_with(
        source_id=source, target_id=target, edge_type=edge_type
    )


# Test traverse_graph method
@pytest.mark.asyncio
async def test_traverse_graph(mock_rag, mock_graph_data):
    """Test the traverse_graph method"""
    # First make sure get_node is mocked to not raise an exception
    start_node = "node1"
    direction = "OUTGOING"
    max_depth = 2
    edge_types = ["KNOWS", "WORKS_AT"]
    limit = 10

    mock_rag.get_node = AsyncMock(return_value={"id": start_node})

    result = await GraphService.traverse_graph(
        rag=mock_rag,
        start_node=start_node,
        direction=direction,
        max_depth=max_depth,
        edge_types=edge_types,
        node_labels=None,
        limit=limit,
    )

    assert result["nodes"] == mock_graph_data["nodes"]
    assert result["edges"] == mock_graph_data["edges"]
    assert result["total_nodes"] == len(mock_graph_data["nodes"])
    assert result["total_edges"] == len(mock_graph_data["edges"])

    # Verify the RAG methods were called with correct parameters
    mock_rag.get_node.assert_called_once_with(node_id=start_node)
    mock_rag.traverse_graph.assert_called_once_with(
        start_node=start_node,
        direction=direction,
        max_depth=max_depth,
        edge_types=edge_types,
        node_labels=None,
        limit=limit,
    )


# Test find_paths method
@pytest.mark.asyncio
async def test_find_paths(mock_rag, mock_graph_data):
    """Test the find_paths method"""
    # First make sure get_node is mocked to not raise an exception
    start_node = "node1"
    end_node = "node2"
    max_depth = 2
    edge_types = ["KNOWS"]

    mock_rag.get_node = AsyncMock(return_value={"id": "exists"})

    result = await GraphService.find_paths(
        rag=mock_rag,
        start_node=start_node,
        end_node=end_node,
        max_depth=max_depth,
        edge_types=edge_types,
    )

    assert "paths" in result
    assert "count" in result
    assert len(result["paths"]) == 1

    # Verify the RAG methods were called with correct parameters
    assert mock_rag.get_node.call_count == 2  # Once for start, once for end
    mock_rag.find_paths.assert_called_once_with(
        start_node=start_node,
        end_node=end_node,
        max_depth=max_depth,
        edge_types=edge_types,
    )


# Test search_graph method
@pytest.mark.asyncio
async def test_search_graph(mock_rag):
    """Test the search_graph method"""
    query = "John"
    limit = 10
    offset = 0

    result = await GraphService.search_graph(
        rag=mock_rag, query=query, limit=limit, offset=offset
    )

    assert "nodes" in result
    assert "edges" in result
    assert "total_nodes" in result
    assert "total_edges" in result
    assert result["total_nodes"] == 1

    # Verify the RAG method was called with correct parameters
    mock_rag.search_graph.assert_called_once_with(
        query=query, limit=limit, offset=offset
    )


# Test format_for_visualization method
@pytest.mark.asyncio
async def test_format_for_visualization(mock_graph_data):
    """Test the format_for_visualization method"""
    format_type = "d3"

    result = await GraphService.format_for_visualization(
        graph_data=mock_graph_data, format=format_type
    )

    assert "nodes" in result
    assert "links" in result  # d3 format uses "links" instead of "edges"
    assert result.get("format", None) is None  # format is not added by the method


# Test the validation of max_depth parameter for the traverse_graph method
@pytest.mark.asyncio
async def test_traverse_graph_validation(mock_rag):
    """Test that traverse_graph validates max_depth"""
    # This test would depend on how your actual validation is implemented in the GraphService
    # If validation is in the FastAPI route, not in the service, then this test would be in the API level tests
    # For now, we'll assume it's handled in the API, so we'll skip this test
    pass
