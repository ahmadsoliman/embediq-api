"""
Documentation API endpoints for EmbedIQ backend.

This module provides API endpoints for serving documentation from Markdown files.
"""

import logging
import os
from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import HTMLResponse
import markdown
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Create router
docs_router = APIRouter(
    prefix="/docs",
    tags=["documentation"],
)

# Get the docs directory path
DOCS_DIR = Path(__file__).parent.parent / "docs"

# CSS for styling the documentation
CSS = """
<style>
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
        line-height: 1.6;
        color: #333;
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
    }
    h1, h2, h3, h4, h5, h6 {
        margin-top: 24px;
        margin-bottom: 16px;
        font-weight: 600;
        line-height: 1.25;
    }
    h1 {
        font-size: 2em;
        border-bottom: 1px solid #eaecef;
        padding-bottom: 0.3em;
    }
    h2 {
        font-size: 1.5em;
        border-bottom: 1px solid #eaecef;
        padding-bottom: 0.3em;
    }
    a {
        color: #0366d6;
        text-decoration: none;
    }
    a:hover {
        text-decoration: underline;
    }
    code {
        font-family: SFMono-Regular, Consolas, 'Liberation Mono', Menlo, monospace;
        background-color: rgba(27, 31, 35, 0.05);
        border-radius: 3px;
        padding: 0.2em 0.4em;
        font-size: 85%;
    }
    pre {
        background-color: #f6f8fa;
        border-radius: 3px;
        padding: 16px;
        overflow: auto;
    }
    pre code {
        background-color: transparent;
        padding: 0;
    }
    blockquote {
        margin: 0;
        padding: 0 1em;
        color: #6a737d;
        border-left: 0.25em solid #dfe2e5;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin-bottom: 16px;
    }
    table th, table td {
        padding: 6px 13px;
        border: 1px solid #dfe2e5;
    }
    table tr {
        background-color: #fff;
        border-top: 1px solid #c6cbd1;
    }
    table tr:nth-child(2n) {
        background-color: #f6f8fa;
    }
    img {
        max-width: 100%;
    }
    .nav {
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 1px solid #eaecef;
    }
    .nav a {
        margin-right: 10px;
    }
</style>
"""

# HTML template for documentation pages
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title} - EmbedIQ Documentation</title>
    {css}
</head>
<body>
    <div class="nav">
        <a href="/api/v1/docs">Documentation Home</a>
        <a href="/">API Home</a>
    </div>
    {content}
</body>
</html>
"""


def get_markdown_files() -> List[Dict[str, Any]]:
    """Get a list of all markdown files in the docs directory."""
    files = []
    for file_path in DOCS_DIR.glob("*.md"):
        files.append({
            "name": file_path.stem,
            "path": file_path.name,
            "full_path": str(file_path),
        })
    return files


def render_markdown_to_html(markdown_content: str) -> str:
    """Convert markdown content to HTML."""
    # Use the Python-Markdown library to convert markdown to HTML
    html = markdown.markdown(
        markdown_content,
        extensions=['tables', 'fenced_code', 'codehilite']
    )
    return html


@docs_router.get("", response_class=HTMLResponse)
async def get_docs_index(request: Request):
    """Get the documentation index page."""
    try:
        # Get the index.md file
        index_path = DOCS_DIR / "index.md"
        
        if not index_path.exists():
            # If index.md doesn't exist, create a simple index page
            files = get_markdown_files()
            content = "<h1>EmbedIQ Documentation</h1>\n<ul>"
            for file in files:
                content += f'<li><a href="/api/v1/docs/{file["name"]}">{file["name"]}</a></li>'
            content += "</ul>"
        else:
            # Read and render the index.md file
            with open(index_path, "r") as f:
                markdown_content = f.read()
            content = render_markdown_to_html(markdown_content)
            
            # Replace relative links with absolute links
            content = content.replace(
                'href="', 
                'href="/api/v1/docs/'
            ).replace(
                'href="/api/v1/docs/http', 
                'href="http'
            )
        
        # Render the HTML template
        html = HTML_TEMPLATE.format(
            title="Documentation Index",
            css=CSS,
            content=content
        )
        
        return HTMLResponse(content=html)
    except Exception as e:
        logger.error(f"Error getting documentation index: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting documentation: {str(e)}"
        )


@docs_router.get("/{doc_name}", response_class=HTMLResponse)
async def get_doc(doc_name: str, request: Request):
    """Get a specific documentation page."""
    try:
        # Handle both with and without .md extension
        if not doc_name.endswith(".md"):
            doc_name = f"{doc_name}.md"
            
        # Get the markdown file
        doc_path = DOCS_DIR / doc_name
        
        if not doc_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Documentation not found: {doc_name}"
            )
            
        # Read and render the markdown file
        with open(doc_path, "r") as f:
            markdown_content = f.read()
        
        content = render_markdown_to_html(markdown_content)
        
        # Replace relative links with absolute links
        content = content.replace(
            'href="', 
            'href="/api/v1/docs/'
        ).replace(
            'href="/api/v1/docs/http', 
            'href="http'
        )
        
        # Get the title from the first heading or use the filename
        title = doc_name.replace(".md", "").replace("_", " ").title()
        if "<h1>" in content:
            title_match = content.split("<h1>")[1].split("</h1>")[0]
            if title_match:
                title = title_match
        
        # Render the HTML template
        html = HTML_TEMPLATE.format(
            title=title,
            css=CSS,
            content=content
        )
        
        return HTMLResponse(content=html)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting documentation {doc_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting documentation: {str(e)}"
        )
