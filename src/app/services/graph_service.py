"""
Service for knowledge graph operations using LightRAG
"""

import logging
from typing import Dict, List, Optional, Any, Union
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class GraphService:
    """
    Service class for knowledge graph operations
    """

    @staticmethod
    async def get_graph(
        rag,
        limit: int = 100,
        offset: int = 0,
        node_labels: Optional[List[str]] = None,
        edge_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get the knowledge graph or a filtered subgraph

        Args:
            rag: The LightRAG instance
            limit: Maximum number of nodes to return
            offset: Number of nodes to skip
            node_labels: Optional list of node labels to filter by
            edge_types: Optional list of edge types to filter by

        Returns:
            Dictionary with nodes and edges
        """
        try:
            logger.info(
                f"Getting graph with filters: labels={node_labels}, edge_types={edge_types}"
            )

            # Call LightRAG to get the graph
            graph = await rag.get_graph(
                limit=limit,
                offset=offset,
                node_labels=node_labels,
                edge_types=edge_types,
            )

            # Format the response
            return {
                "nodes": graph.get("nodes", []),
                "edges": graph.get("edges", []),
                "total_nodes": len(graph.get("nodes", [])),
                "total_edges": len(graph.get("edges", [])),
            }
        except Exception as e:
            logger.error(f"Error getting graph: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting graph: {str(e)}",
            )

    @staticmethod
    async def get_node(rag, node_id: str) -> Dict[str, Any]:
        """
        Get a specific node by ID

        Args:
            rag: The LightRAG instance
            node_id: ID of the node to retrieve

        Returns:
            Node data
        """
        try:
            logger.info(f"Getting node with ID: {node_id}")

            # Call LightRAG to get the node
            node = await rag.get_node(node_id=node_id)

            if not node:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Node with ID {node_id} not found",
                )

            return node
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting node {node_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting node: {str(e)}",
            )

    @staticmethod
    async def create_node(
        rag, label: str, properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new node in the knowledge graph

        Args:
            rag: The LightRAG instance
            label: Label for the node
            properties: Properties for the node

        Returns:
            Created node data with ID
        """
        try:
            logger.info(f"Creating node with label: {label}")

            # Call LightRAG to create the node
            node = await rag.create_node(label=label, properties=properties)

            return node
        except Exception as e:
            logger.error(f"Error creating node: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating node: {str(e)}",
            )

    @staticmethod
    async def update_node(
        rag,
        node_id: str,
        label: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Update an existing node

        Args:
            rag: The LightRAG instance
            node_id: ID of the node to update
            label: New label for the node (optional)
            properties: New properties for the node (optional)

        Returns:
            Updated node data
        """
        try:
            logger.info(f"Updating node with ID: {node_id}")

            # Get the current node
            current_node = await GraphService.get_node(rag, node_id)

            # Prepare the update data
            update_data = {}
            if label:
                update_data["label"] = label

            if properties is not None:
                update_data["properties"] = properties

            # Call LightRAG to update the node
            updated_node = await rag.update_node(node_id=node_id, **update_data)

            return updated_node
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating node {node_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating node: {str(e)}",
            )

    @staticmethod
    async def delete_node(rag, node_id: str) -> Dict[str, Any]:
        """
        Delete a node from the knowledge graph

        Args:
            rag: The LightRAG instance
            node_id: ID of the node to delete

        Returns:
            Deletion result
        """
        try:
            logger.info(f"Deleting node with ID: {node_id}")

            # Verify the node exists
            await GraphService.get_node(rag, node_id)

            # Call LightRAG to delete the node
            result = await rag.delete_node(node_id=node_id)

            return {
                "id": node_id,
                "deleted": True,
                "affected_edges": result.get("affected_edges", 0),
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting node {node_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting node: {str(e)}",
            )

    @staticmethod
    async def create_edge(
        rag, source: str, target: str, edge_type: str, properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new edge between nodes

        Args:
            rag: The LightRAG instance
            source: ID of the source node
            target: ID of the target node
            edge_type: Type of the edge
            properties: Properties for the edge

        Returns:
            Created edge data
        """
        try:
            logger.info(f"Creating edge from {source} to {target} of type {edge_type}")

            # Verify source and target nodes exist
            await GraphService.get_node(rag, source)
            await GraphService.get_node(rag, target)

            # Call LightRAG to create the edge
            edge = await rag.create_edge(
                source_id=source,
                target_id=target,
                edge_type=edge_type,
                properties=properties,
            )

            return edge
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating edge: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating edge: {str(e)}",
            )

    @staticmethod
    async def update_edge(
        rag,
        source: str,
        target: str,
        edge_type: str,
        new_type: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Update an existing edge

        Args:
            rag: The LightRAG instance
            source: ID of the source node
            target: ID of the target node
            edge_type: Current type of the edge
            new_type: New type for the edge (optional)
            properties: New properties for the edge (optional)

        Returns:
            Updated edge data
        """
        try:
            logger.info(f"Updating edge from {source} to {target} of type {edge_type}")

            # Prepare the update data
            update_data = {}
            if new_type:
                update_data["new_type"] = new_type

            if properties is not None:
                update_data["properties"] = properties

            # Call LightRAG to update the edge
            edge = await rag.update_edge(
                source_id=source, target_id=target, edge_type=edge_type, **update_data
            )

            return edge
        except Exception as e:
            logger.error(f"Error updating edge: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating edge: {str(e)}",
            )

    @staticmethod
    async def delete_edge(
        rag, source: str, target: str, edge_type: str
    ) -> Dict[str, Any]:
        """
        Delete an edge from the knowledge graph

        Args:
            rag: The LightRAG instance
            source: ID of the source node
            target: ID of the target node
            edge_type: Type of the edge

        Returns:
            Deletion result
        """
        try:
            logger.info(f"Deleting edge from {source} to {target} of type {edge_type}")

            # Call LightRAG to delete the edge
            await rag.delete_edge(
                source_id=source, target_id=target, edge_type=edge_type
            )

            return {
                "source": source,
                "target": target,
                "type": edge_type,
                "deleted": True,
            }
        except Exception as e:
            logger.error(f"Error deleting edge: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting edge: {str(e)}",
            )

    @staticmethod
    async def traverse_graph(
        rag,
        start_node: str,
        direction: str,
        max_depth: int,
        edge_types: Optional[List[str]] = None,
        node_labels: Optional[List[str]] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        Traverse the graph starting from a specific node

        Args:
            rag: The LightRAG instance
            start_node: ID of the node to start from
            direction: Direction of traversal (outbound, inbound, any)
            max_depth: Maximum traversal depth
            edge_types: Optional list of edge types to traverse
            node_labels: Optional list of node labels to include
            limit: Maximum number of nodes to return

        Returns:
            Subgraph with nodes and edges
        """
        try:
            logger.info(
                f"Traversing graph from node {start_node} with depth {max_depth}"
            )

            # Verify start node exists
            await GraphService.get_node(rag, start_node)

            # Call LightRAG to traverse the graph
            subgraph = await rag.traverse_graph(
                start_node=start_node,
                direction=direction,
                max_depth=max_depth,
                edge_types=edge_types,
                node_labels=node_labels,
                limit=limit,
            )

            # Format the response
            return {
                "nodes": subgraph.get("nodes", []),
                "edges": subgraph.get("edges", []),
                "total_nodes": len(subgraph.get("nodes", [])),
                "total_edges": len(subgraph.get("edges", [])),
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error traversing graph: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error traversing graph: {str(e)}",
            )

    @staticmethod
    async def find_paths(
        rag,
        start_node: str,
        end_node: str,
        max_depth: int,
        edge_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Find paths between two nodes

        Args:
            rag: The LightRAG instance
            start_node: ID of the start node
            end_node: ID of the end node
            max_depth: Maximum path length
            edge_types: Optional list of edge types to follow

        Returns:
            List of paths between the nodes
        """
        try:
            logger.info(
                f"Finding paths from {start_node} to {end_node} with max depth {max_depth}"
            )

            # Verify nodes exist
            await GraphService.get_node(rag, start_node)
            await GraphService.get_node(rag, end_node)

            # Call LightRAG to find paths
            paths = await rag.find_paths(
                start_node=start_node,
                end_node=end_node,
                max_depth=max_depth,
                edge_types=edge_types,
            )

            return {"paths": paths, "count": len(paths)}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error finding paths: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error finding paths: {str(e)}",
            )

    @staticmethod
    async def search_graph(
        rag, query: str, limit: int = 10, offset: int = 0
    ) -> Dict[str, Any]:
        """
        Perform a semantic search in the knowledge graph

        Args:
            rag: The LightRAG instance
            query: Search query
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Subgraph with nodes and edges matching the query
        """
        try:
            logger.info(f"Searching graph with query: {query}")

            # Call LightRAG to search the graph
            results = await rag.search_graph(query=query, limit=limit, offset=offset)

            # Format the response
            return {
                "nodes": results.get("nodes", []),
                "edges": results.get("edges", []),
                "total_nodes": len(results.get("nodes", [])),
                "total_edges": len(results.get("edges", [])),
            }
        except Exception as e:
            logger.error(f"Error searching graph: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error searching graph: {str(e)}",
            )

    @staticmethod
    async def format_for_visualization(
        graph_data: Dict[str, Any], format: str
    ) -> Dict[str, Any]:
        """
        Format graph data for visualization libraries

        Args:
            graph_data: Graph data with nodes and edges
            format: Desired format (d3, cytoscape, jsonld)

        Returns:
            Formatted graph data
        """
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])

        if format == "d3":
            return {
                "nodes": [
                    {
                        "id": node.get("id"),
                        "label": node.get("label"),
                        "group": node.get("label"),
                        **node.get("properties", {}),
                    }
                    for node in nodes
                ],
                "links": [
                    {
                        "source": edge.get("source"),
                        "target": edge.get("target"),
                        "type": edge.get("type"),
                        "value": 1,
                        **edge.get("properties", {}),
                    }
                    for edge in edges
                ],
            }
        elif format == "cytoscape":
            return {
                "elements": {
                    "nodes": [
                        {
                            "data": {
                                "id": node.get("id"),
                                "label": node.get("label"),
                                **node.get("properties", {}),
                            }
                        }
                        for node in nodes
                    ],
                    "edges": [
                        {
                            "data": {
                                "id": f"{edge.get('source')}-{edge.get('type')}-{edge.get('target')}",
                                "source": edge.get("source"),
                                "target": edge.get("target"),
                                "label": edge.get("type"),
                                **edge.get("properties", {}),
                            }
                        }
                        for edge in edges
                    ],
                }
            }
        elif format == "jsonld":
            # JSON-LD format
            context = {
                "@context": {
                    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                    "xsd": "http://www.w3.org/2001/XMLSchema#",
                    "label": "rdfs:label",
                    "type": "rdf:type",
                    "property": "rdf:Property",
                }
            }

            graph = []

            # Add nodes
            for node in nodes:
                node_obj = {
                    "@id": node.get("id"),
                    "type": node.get("label"),
                    "label": node.get("label"),
                }

                # Add properties
                for key, value in node.get("properties", {}).items():
                    node_obj[key] = value

                graph.append(node_obj)

            # Add edges
            for edge in edges:
                edge_obj = {
                    "@id": f"{edge.get('source')}-{edge.get('type')}-{edge.get('target')}",
                    "type": "property",
                    "label": edge.get("type"),
                    "source": {"@id": edge.get("source")},
                    "target": {"@id": edge.get("target")},
                }

                # Add properties
                for key, value in edge.get("properties", {}).items():
                    edge_obj[key] = value

                graph.append(edge_obj)

            return {**context, "@graph": graph}
        else:
            # Default format - just return the original data
            return graph_data
