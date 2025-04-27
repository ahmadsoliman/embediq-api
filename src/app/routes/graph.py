"""
API routes for knowledge graph operations
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
    Path,
    Header,
    Response,
    Body,
)
from typing import List, Optional, Dict, Any, Type, Callable
from uuid import UUID
import logging
from fastapi.responses import JSONResponse

from app.middleware.auth import validate_token
from app.models.graph import (
    GraphNode,
    GraphNodeCreate,
    GraphNodeUpdate,
    GraphEdge,
    GraphEdgeCreate,
    GraphEdgeUpdate,
    GraphResponse,
    GraphSearchRequest,
    GraphTraversalRequest,
    GraphPathRequest,
    GraphPathResponse,
    NodeDeleteResponse,
    EdgeDeleteResponse,
    VisualizationFormatEnum,
    GraphVisualizationRequest,
    DirectionEnum,
)
from app.services.graph_service import GraphService
from app.dependencies import get_rag_for_user

# Create graph router - remove the prefix since api_router already has it
graph_router = APIRouter(tags=["graph"])

logger = logging.getLogger(__name__)


# Service factory function - created inline to replace the missing utils.service_factory
def service_factory(service_class: Type) -> Callable:
    """Return a function that returns an instance of the service class"""

    def get_service():
        return service_class()

    return get_service


# Get the current graph service using the factory
get_graph_service = service_factory(GraphService)


@graph_router.get(
    "",
    response_model=GraphResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the knowledge graph",
    description="Retrieve the knowledge graph or a filtered subgraph.",
)
async def get_graph(
    limit: int = Query(
        100, ge=1, le=500, description="Maximum number of nodes to return"
    ),
    offset: int = Query(0, ge=0, description="Number of nodes to skip"),
    node_labels: Optional[List[str]] = Query(None, description="Filter by node labels"),
    edge_types: Optional[List[str]] = Query(None, description="Filter by edge types"),
    graph_service: GraphService = Depends(get_graph_service),
    user_id: str = Depends(validate_token),
):
    """
    Get the knowledge graph or a filtered subgraph.

    This endpoint returns the knowledge graph with optional filters.
    Due to performance reasons, the maximum number of nodes is limited to 500.

    Parameters:
    - limit: Maximum number of nodes to return (default: 100, max: 500)
    - offset: Number of nodes to skip for pagination (default: 0)
    - node_labels: Optional list of node labels to filter by
    - edge_types: Optional list of edge types to filter by
    """
    # Ensure limit doesn't exceed 500 nodes to prevent performance issues
    if limit > 500:
        limit = 500

    return await graph_service.get_graph(
        limit=limit, offset=offset, node_labels=node_labels, edge_types=edge_types
    )


# This endpoint aligns with LightRAG's API, which provides a /graphs endpoint
# that takes a label and max_depth parameter to get a knowledge graph.
@graph_router.get(
    "/graphs",
    response_model=GraphResponse,
    status_code=status.HTTP_200_OK,
    summary="Get knowledge graph by label",
    description="Get a knowledge graph for a specific node label with limited depth.",
)
async def get_knowledge_graph(
    label: str = Query(..., description="Node label to get graph for"),
    max_depth: int = Query(
        3, ge=1, le=3, description="Maximum traversal depth (max 3)"
    ),
    rag=Depends(get_rag_for_user),
    user_id: str = Depends(validate_token),
):
    """
    Get a knowledge graph centered around nodes with a specific label.

    This endpoint directly maps to LightRAG's get_knowledge_graph function,
    which retrieves a subgraph containing nodes with the specified label
    and their connections up to the specified depth.
    """
    try:
        # Call LightRAG's get_knowledge_graph function
        graph = await rag.get_knowledge_graph(node_label=label, max_depth=max_depth)

        # Format the response
        return {
            "nodes": graph.get("nodes", []),
            "edges": graph.get("edges", []),
            "total_nodes": len(graph.get("nodes", [])),
            "total_edges": len(graph.get("edges", [])),
        }
    except Exception as e:
        logger.error(f"Error getting knowledge graph: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting knowledge graph: {str(e)}",
        )


@graph_router.get(
    "/nodes/{node_id}",
    response_model=GraphNode,
    status_code=status.HTTP_200_OK,
    summary="Get a specific node",
    description="Retrieve a specific node by its ID.",
)
async def get_node(
    node_id: str = Path(..., description="Node ID"),
    rag=Depends(get_rag_for_user),
    user_id: str = Depends(validate_token),
):
    """
    Get a specific node from the knowledge graph.

    This endpoint returns a single node identified by its ID.
    """
    node = await GraphService.get_node(rag=rag, node_id=node_id)
    return node


@graph_router.post(
    "/nodes",
    response_model=GraphNode,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new node",
    description="Create a new node in the knowledge graph.",
)
async def create_node(
    node: GraphNodeCreate,
    rag=Depends(get_rag_for_user),
    user_id: str = Depends(validate_token),
):
    """
    Create a new node in the knowledge graph.

    This endpoint creates a new node with the specified label and properties.
    """
    created_node = await GraphService.create_node(
        rag=rag,
        label=node.label,
        properties=node.properties,
    )

    return created_node


@graph_router.patch(
    "/nodes/{node_id}",
    response_model=GraphNode,
    status_code=status.HTTP_200_OK,
    summary="Update a node",
    description="Update an existing node in the knowledge graph.",
)
async def update_node(
    node: GraphNodeUpdate,
    node_id: str = Path(..., description="Node ID"),
    rag=Depends(get_rag_for_user),
    user_id: str = Depends(validate_token),
):
    """
    Update an existing node in the knowledge graph.

    This endpoint updates a node's label and/or properties.
    """
    updated_node = await GraphService.update_node(
        rag=rag,
        node_id=node_id,
        label=node.label,
        properties=node.properties,
    )

    return updated_node


@graph_router.delete(
    "/nodes/{node_id}",
    response_model=NodeDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a node",
    description="Delete a node from the knowledge graph.",
)
async def delete_node(
    node_id: str = Path(..., description="Node ID"),
    rag=Depends(get_rag_for_user),
    user_id: str = Depends(validate_token),
):
    """
    Delete a node from the knowledge graph.

    This endpoint deletes a node and all its connected edges.
    """
    result = await GraphService.delete_node(rag=rag, node_id=node_id)
    return result


@graph_router.post(
    "/edges",
    response_model=GraphEdge,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new edge",
    description="Create a new edge between nodes in the knowledge graph.",
)
async def create_edge(
    edge: GraphEdgeCreate,
    rag=Depends(get_rag_for_user),
    user_id: str = Depends(validate_token),
):
    """
    Create a new edge between nodes in the knowledge graph.

    This endpoint creates a relationship between two existing nodes.
    """
    created_edge = await GraphService.create_edge(
        rag=rag,
        source=edge.source,
        target=edge.target,
        edge_type=edge.type,
        properties=edge.properties,
    )

    return created_edge


@graph_router.patch(
    "/edges",
    response_model=GraphEdge,
    status_code=status.HTTP_200_OK,
    summary="Update an edge",
    description="Update an existing edge in the knowledge graph.",
)
async def update_edge(
    current_source: str = Query(..., description="Source node ID"),
    current_target: str = Query(..., description="Target node ID"),
    current_type: str = Query(..., description="Current edge type"),
    update_data: GraphEdgeUpdate = Body(...),
    rag=Depends(get_rag_for_user),
    user_id: str = Depends(validate_token),
):
    """
    Update an existing edge in the knowledge graph.

    This endpoint updates an edge's type and/or properties.
    """
    updated_edge = await GraphService.update_edge(
        rag=rag,
        source=current_source,
        target=current_target,
        edge_type=current_type,
        new_type=update_data.type,
        properties=update_data.properties,
    )

    return updated_edge


@graph_router.delete(
    "/edges",
    response_model=EdgeDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete an edge",
    description="Delete an edge from the knowledge graph.",
)
async def delete_edge(
    source: str = Query(..., description="Source node ID"),
    target: str = Query(..., description="Target node ID"),
    type: str = Query(..., description="Edge type"),
    rag=Depends(get_rag_for_user),
    user_id: str = Depends(validate_token),
):
    """
    Delete an edge from the knowledge graph.

    This endpoint deletes a relationship between nodes.
    """
    result = await GraphService.delete_edge(
        rag=rag,
        source=source,
        target=target,
        edge_type=type,
    )

    return result


@graph_router.post(
    "/traverse",
    response_model=GraphResponse,
    status_code=status.HTTP_200_OK,
    summary="Traverse the graph",
    description="Traverse the graph starting from a specific node.",
)
async def traverse_graph(
    traversal: GraphTraversalRequest,
    rag=Depends(get_rag_for_user),
    user_id: str = Depends(validate_token),
):
    """
    Traverse the graph starting from a specific node.

    This endpoint returns a subgraph by traversing from a start node
    following the specified direction and edge types.
    Limited to a maximum depth of 3 as recommended by LightRAG.
    """
    result = await GraphService.traverse_graph(
        rag=rag,
        start_node=traversal.node_id,
        direction=traversal.direction.value,
        max_depth=traversal.max_depth,
        edge_types=traversal.edge_types,
        node_labels=traversal.node_labels,
        limit=traversal.limit,
    )

    return result


@graph_router.post(
    "/paths",
    response_model=GraphPathResponse,
    status_code=status.HTTP_200_OK,
    summary="Find paths between nodes",
    description="Find paths between two nodes in the knowledge graph.",
)
async def find_paths(
    path_request: GraphPathRequest,
    rag=Depends(get_rag_for_user),
    user_id: str = Depends(validate_token),
):
    """
    Find paths between two nodes in the knowledge graph.

    This endpoint returns all paths between two nodes up to a maximum depth.
    Limited to a maximum depth of 3 as recommended by LightRAG.
    """
    result = await GraphService.find_paths(
        rag=rag,
        start_node=path_request.source_id,
        end_node=path_request.target_id,
        max_depth=path_request.max_depth,
        edge_types=path_request.edge_types,
    )

    return result


@graph_router.post(
    "/search",
    response_model=GraphResponse,
    status_code=status.HTTP_200_OK,
    summary="Search the knowledge graph",
    description="Perform a semantic search in the knowledge graph.",
)
async def search_graph(
    search_request: GraphSearchRequest,
    rag=Depends(get_rag_for_user),
    user_id: str = Depends(validate_token),
):
    """
    Perform a semantic search in the knowledge graph.

    This endpoint searches the graph using semantic similarity
    to find nodes and edges matching the query.
    """
    result = await GraphService.search_graph(
        rag=rag,
        query=search_request.query,
        limit=search_request.limit,
        offset=search_request.offset,
    )

    return result


@graph_router.get(
    "/visualize",
    summary="Get visualization-friendly graph data",
    description="Get graph data formatted for visualization libraries.",
)
async def get_visualization_data(
    format: VisualizationFormatEnum = Query(
        VisualizationFormatEnum.DEFAULT, description="Visualization format"
    ),
    limit: int = Query(
        100, ge=1, le=500, description="Maximum number of nodes (max 500)"
    ),
    node_labels: Optional[str] = Query(
        None, description="Filter by node labels (comma-separated)"
    ),
    edge_types: Optional[str] = Query(
        None, description="Filter by edge types (comma-separated)"
    ),
    accept: Optional[str] = Header(None),
    rag=Depends(get_rag_for_user),
    user_id: str = Depends(validate_token),
):
    """
    Get graph data formatted for visualization libraries.

    This endpoint returns graph data in formats compatible with
    common visualization libraries like D3.js and Cytoscape.js.
    Limited to 500 nodes maximum to prevent performance issues.
    """
    # Check for JSON-LD in Accept header
    if accept and "application/ld+json" in accept:
        format = VisualizationFormatEnum.JSONLD

    # Convert comma-separated strings to lists
    node_label_list = node_labels.split(",") if node_labels else None
    edge_type_list = edge_types.split(",") if edge_types else None

    # Get the graph data
    graph_data = await GraphService.get_graph(
        rag=rag,
        limit=limit,
        offset=0,
        node_labels=node_label_list,
        edge_types=edge_type_list,
    )

    # Format the data for visualization
    viz_data = await GraphService.format_for_visualization(
        graph_data=graph_data,
        format=format.value,
    )

    # Return with appropriate content type
    if format == VisualizationFormatEnum.JSONLD:
        return Response(content=str(viz_data), media_type="application/ld+json")

    return viz_data
