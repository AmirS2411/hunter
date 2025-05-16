#!/usr/bin/env python3
import asyncio
import os
import json
import logging
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from hunter_api import HunterAPI

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Change to DEBUG for more detailed logs
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("hunter-mcp")

# Add console handler for immediate feedback
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
logger.addHandler(console_handler)

# Initialize the Hunter API client
api_key = os.environ.get("HUNTER_API_KEY")
if not api_key:
    logger.error("HUNTER_API_KEY environment variable is not set")
    logger.error("Please add your API key to the .env file")
    exit(1)

hunter_api = HunterAPI(api_key)

# Create the FastAPI app
app = FastAPI(
    title="Hunter MCP Server", 
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware with more specific configuration for Shortwave
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # Specify allowed methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["Content-Type", "Content-Length"],
    max_age=600  # Cache preflight requests for 10 minutes
)

# Root endpoint for testing
@app.get("/")
async def root():
    return {
        "message": "Hunter MCP Server is running",
        "version": "1.0.0",
        "endpoints": [
            "/sse - Server-Sent Events endpoint for MCP",
            "/tools/list - List available tools",
            "/tools/call - Call a tool",
            "/resources/list - List available resources",
            "/resources/read - Read a resource"
        ]
    }

# Define MCP tools
TOOLS = [
    {
        "name": "email_finder",
        "description": "Find the most likely email address from a domain name, first name, and last name",
        "inputSchema": {
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "The domain name of the company (e.g., 'google.com')"},
                "first_name": {"type": "string", "description": "The first name of the person"},
                "last_name": {"type": "string", "description": "The last name of the person"},
                "company": {"type": "string", "description": "Optional company name if domain is not provided"},
                "full_name": {"type": "string", "description": "Optional full name if first and last name are not provided separately"}
            },
            "required": ["domain"],
            "anyOf": [
                {"required": ["first_name", "last_name"]},
                {"required": ["full_name"]}
            ]
        },
        "annotations": {
            "title": "Find Email Address",
            "readOnlyHint": True,
            "idempotentHint": True,
            "openWorldHint": True
        }
    },
    {
        "name": "email_verifier",
        "description": "Verify the deliverability of an email address",
        "inputSchema": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "The email address to verify"}
            },
            "required": ["email"]
        },
        "annotations": {
            "title": "Verify Email Address",
            "readOnlyHint": True,
            "idempotentHint": True,
            "openWorldHint": True
        }
    },
    {
        "name": "domain_search",
        "description": "Find email addresses from a domain name",
        "inputSchema": {
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "The domain name to search (e.g., 'google.com')"},
                "limit": {"type": "integer", "description": "Maximum number of results to return (default: 10)"},
                "type": {"type": "string", "description": "Type of emails to return (personal or generic)", "enum": ["personal", "generic"]}
            },
            "required": ["domain"]
        },
        "annotations": {
            "title": "Search Domain for Emails",
            "readOnlyHint": True,
            "idempotentHint": True,
            "openWorldHint": True
        }
    }
]

# Define MCP resources
RESOURCES = [
    {
        "uri": "hunter://api-info",
        "title": "Hunter API Information",
        "description": "Information about the Hunter API and available endpoints"
    }
]

# MCP API endpoints
@app.get("/tools/list")
async def list_tools():
    """List available tools for the Hunter API."""
    return {"tools": TOOLS}

@app.post("/tools/call")
async def call_tool(request: Request):
    """Handle tool execution."""
    data = await request.json()
    name = data.get("name")
    arguments = data.get("arguments", {})
    
    logger.info(f"Tool call: {name} with arguments {arguments}")
    
    try:
        if name == "email_finder":
            result = await hunter_api.find_email(**arguments)
            return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
        
        elif name == "email_verifier":
            result = await hunter_api.verify_email(arguments["email"])
            return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
        
        elif name == "domain_search":
            limit = arguments.get("limit", 10)
            email_type = arguments.get("type")
            result = await hunter_api.domain_search(arguments["domain"], limit=limit, type=email_type)
            return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
        
        else:
            return JSONResponse(status_code=404, content={"error": f"Unknown tool: {name}"})
    
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/resources/list")
async def list_resources():
    """List available resources."""
    return {"resources": RESOURCES}

@app.get("/resources/read")
async def read_resource(uri: str):
    """Read a resource."""
    if uri == "hunter://api-info":
        content = """
# Hunter API

Hunter is an email finding and verification service that allows you to:
- Find email addresses from a domain name
- Verify the deliverability of email addresses
- Find the most likely email address from a domain name, first name, and last name

## Available Tools

1. **email_finder** - Find the most likely email address from a domain name, first name, and last name
2. **email_verifier** - Verify the deliverability of an email address
3. **domain_search** - Find email addresses from a domain name

## API Documentation
For more information, visit: https://hunter.io/api-documentation/v2
"""
        return {"type": "text/markdown", "data": content}
    
    return JSONResponse(status_code=404, content={"error": f"Unknown resource: {uri}"})

# SSE endpoint for MCP
@app.get("/sse")
async def sse_endpoint(request: Request):
    """Server-Sent Events endpoint for MCP."""
    client_host = getattr(request.client, 'host', 'unknown')
    logger.info(f"SSE connection requested from {client_host}")
    
    # Handle OPTIONS requests for CORS preflight
    if request.method == "OPTIONS":
        return JSONResponse(
            content={"status": "ok"},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Max-Age": "86400",
            }
        )
    
    async def event_generator():
        try:
            # Initial connection event
            logger.info("Sending connected event")
            yield {"event": "connected", "data": json.dumps({"server": "hunter-mcp", "version": "1.0.0"})}
            await asyncio.sleep(0.1)  # Small delay between events
            
            # Send capabilities message
            logger.info("Sending capabilities event")
            yield {"event": "capabilities", "data": json.dumps({
                "tools": True,
                "resources": True,
                "logging": True
            })}
            await asyncio.sleep(0.1)  # Small delay between events
            
            # Send initialization complete message
            logger.info("Sending initialization_complete event")
            yield {"event": "initialization_complete", "data": json.dumps({})}
            await asyncio.sleep(0.1)  # Small delay between events
            
            # Keep connection alive
            count = 0
            while True:
                await asyncio.sleep(10)  # Less frequent pings to reduce load
                count += 1
                logger.debug(f"Sending ping event {count}")
                yield {"event": "ping", "data": json.dumps({"timestamp": asyncio.get_event_loop().time()})}
        except asyncio.CancelledError:
            logger.info("SSE connection was cancelled")
        except Exception as e:
            logger.error(f"Error in SSE event generator: {e}")
            raise
    
    headers = {
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
        "Content-Type": "text/event-stream",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "*"
    }
    
    try:
        return EventSourceResponse(
            event_generator(), 
            media_type="text/event-stream",
            headers=headers,
            ping=10  # Send a ping every 10 seconds
        )
    except Exception as e:
        logger.error(f"Error creating EventSourceResponse: {e}")
        raise

# Run the server
def start():
    """Run the MCP server using uvicorn."""
    import uvicorn
    logger.info("Starting Hunter MCP server")
    
    # Get port from environment variable (for cloud deployment) or use default
    port = int(os.environ.get("PORT", 8088))
    logger.info(f"Starting server on port {port}")
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=port)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        print(f"Error starting server: {e}")
        # Try another port if the first one is in use
        try:
            alternate_port = port + 1
            logger.info(f"Trying alternate port {alternate_port}...")
            uvicorn.run(app, host="0.0.0.0", port=alternate_port)
        except Exception as e:
            logger.error(f"Error starting server on alternate port: {e}")
            print(f"Error starting server on alternate port: {e}")

if __name__ == "__main__":
    start()
