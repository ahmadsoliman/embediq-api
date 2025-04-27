"""
Models for the knowledge graph API
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from uuid import UUID
import json


class DirectionEnum(str, Enum):
    """Direction enum for graph traversal"""

    OUTBOUND = "outbound"
    INBOUND = "inbound"
    ANY = "any"


class GraphTraversalDirection(str, Enum):
    """
    Enum for graph traversal direction

    Defines the possible directions for traversing edges in the knowledge graph.
    """

    OUTGOING = "OUTGOING"  # Follow outgoing edges from the node
    INCOMING = "INCOMING"  # Follow incoming edges to the node
    BOTH = "BOTH"  # Follow both incoming and outgoing edges


class GraphNode(BaseModel):
    """Model representing a node in the knowledge graph"""

    id: str
    label: str
    properties: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        schema_extra = {
            "example": {
                "id": "1234",
                "label": "Person",
                "properties": {"name": "John Doe", "age": 30},
            }
        }


class GraphEdge(BaseModel):
    """Model representing an edge (relationship) in the knowledge graph"""

    source: str
    target: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        schema_extra = {
            "example": {
                "source": "1234",
                "target": "5678",
                "type": "KNOWS",
                "properties": {"since": "2020-01-01", "strength": 0.8},
            }
        }


class GraphNodeCreate(BaseModel):
    """Model for creating a new node"""

    label: str
    properties: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        schema_extra = {
            "example": {
                "label": "Person",
                "properties": {"name": "John Doe", "age": 30},
            }
        }


class GraphEdgeCreate(BaseModel):
    """Model for creating a new edge"""

    source: str
    target: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        schema_extra = {
            "example": {
                "source": "1234",
                "target": "5678",
                "type": "KNOWS",
                "properties": {"since": "2020-01-01", "strength": 0.8},
            }
        }


class GraphNodeUpdate(BaseModel):
    """Model for updating an existing node"""

    label: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None

    class Config:
        schema_extra = {
            "example": {
                "label": "Person",
                "properties": {"name": "John Smith", "age": 32},
            }
        }

    @validator("properties", pre=True)
    def validate_properties(cls, v):
        """Validate that properties are not None"""
        return v or {}


class GraphEdgeUpdate(BaseModel):
    """Model for updating an existing edge"""

    type: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None

    class Config:
        schema_extra = {
            "example": {
                "type": "KNOWS_WELL",
                "properties": {"since": "2018-01-01", "strength": 0.9},
            }
        }

    @validator("properties", pre=True)
    def validate_properties(cls, v):
        """Validate that properties are not None"""
        return v or {}


class GraphResponse(BaseModel):
    """Model for returning a subgraph"""

    nodes: List[GraphNode]
    edges: List[GraphEdge]
    total_nodes: int
    total_edges: int

    class Config:
        schema_extra = {
            "example": {
                "nodes": [
                    {
                        "id": "1234",
                        "label": "Person",
                        "properties": {"name": "John Doe"},
                    },
                    {
                        "id": "5678",
                        "label": "Person",
                        "properties": {"name": "Jane Smith"},
                    },
                ],
                "edges": [
                    {
                        "source": "1234",
                        "target": "5678",
                        "type": "KNOWS",
                        "properties": {},
                    }
                ],
                "total_nodes": 2,
                "total_edges": 1,
            }
        }


class GraphSearchRequest(BaseModel):
    """Model for graph search requests"""

    query: str
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    class Config:
        schema_extra = {
            "example": {"query": "John works at Company", "limit": 10, "offset": 0}
        }


class GraphTraversalRequest(BaseModel):
    """
    Request model for graph traversal operations

    This model defines the parameters for traversing the knowledge graph
    starting from a specified node and following edges in the specified direction.
    """

    node_id: str = Field(..., description="ID of the starting node")
    direction: GraphTraversalDirection = Field(
        GraphTraversalDirection.OUTGOING,
        description="Direction of traversal (OUTGOING, INCOMING, BOTH)",
    )
    max_depth: int = Field(
        2, ge=1, le=3, description="Maximum traversal depth (1-3, default: 2)"
    )
    edge_types: Optional[List[str]] = Field(
        None, description="Types of edges to include in traversal"
    )
    node_labels: Optional[List[str]] = Field(
        None, description="Labels of nodes to include in traversal"
    )
    limit: int = Field(
        100, ge=1, le=500, description="Maximum number of nodes to return (max 500)"
    )
    include_root: bool = Field(
        True, description="Whether to include the root node in the result"
    )

    class Config:
        schema_extra = {
            "example": {
                "node_id": "node1",
                "direction": "OUTGOING",
                "max_depth": 2,
                "edge_types": ["RELATES_TO", "REFERENCES"],
                "node_labels": ["Document", "Entity"],
                "limit": 50,
                "include_root": True,
            }
        }


class GraphPathRequest(BaseModel):
    """
    Request model for finding shortest paths between nodes

    This model defines the parameters for finding paths between
    a source node and a target node in the knowledge graph.
    """

    source_id: str = Field(..., description="ID of the source node")
    target_id: str = Field(..., description="ID of the target node")
    max_depth: int = Field(
        2, ge=1, le=3, description="Maximum path depth (1-3, default: 2)"
    )
    edge_types: Optional[List[str]] = Field(
        None, description="Types of edges to include in path finding"
    )
    limit: int = Field(
        5, ge=1, le=10, description="Maximum number of paths to return (max 10)"
    )

    class Config:
        schema_extra = {
            "example": {
                "source_id": "node1",
                "target_id": "node2",
                "max_depth": 2,
                "edge_types": ["RELATES_TO", "REFERENCES"],
                "limit": 5,
            }
        }


class GraphPathResponse(BaseModel):
    """Model for returning paths between nodes"""

    paths: List[Dict[str, Any]]
    count: int

    class Config:
        schema_extra = {
            "example": {
                "paths": [
                    {
                        "nodes": [
                            {
                                "id": "1234",
                                "label": "Person",
                                "properties": {"name": "John"},
                            },
                            {
                                "id": "9012",
                                "label": "Person",
                                "properties": {"name": "Alice"},
                            },
                            {
                                "id": "5678",
                                "label": "Person",
                                "properties": {"name": "Jane"},
                            },
                        ],
                        "edges": [
                            {
                                "source": "1234",
                                "target": "9012",
                                "type": "KNOWS",
                                "properties": {},
                            },
                            {
                                "source": "9012",
                                "target": "5678",
                                "type": "WORKS_WITH",
                                "properties": {},
                            },
                        ],
                        "length": 2,
                    }
                ],
                "count": 1,
            }
        }


class NodeDeleteResponse(BaseModel):
    """Response model for node deletion"""

    id: str
    deleted: bool
    affected_edges: int

    class Config:
        schema_extra = {"example": {"id": "1234", "deleted": True, "affected_edges": 3}}


class EdgeDeleteResponse(BaseModel):
    """Response model for edge deletion"""

    source: str
    target: str
    type: str
    deleted: bool

    class Config:
        schema_extra = {
            "example": {
                "source": "1234",
                "target": "5678",
                "type": "KNOWS",
                "deleted": True,
            }
        }


class VisualizationFormatEnum(str, Enum):
    """Supported visualization formats"""

    D3 = "d3"
    CYTOSCAPE = "cytoscape"
    JSONLD = "jsonld"
    DEFAULT = "default"


class GraphVisualizationRequest(BaseModel):
    """Request model for graph visualization"""

    format: VisualizationFormatEnum = VisualizationFormatEnum.DEFAULT
    limit: int = Field(default=100, ge=1, le=500)
    node_labels: Optional[List[str]] = None
    edge_types: Optional[List[str]] = None

    class Config:
        schema_extra = {
            "example": {
                "format": "d3",
                "limit": 100,
                "node_labels": ["Person", "Company"],
                "edge_types": ["KNOWS", "WORKS_AT"],
            }
        }
