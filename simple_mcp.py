#!/usr/bin/env python3
import os
import json
import logging
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from hunter_api import HunterAPI

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("hunter-mcp-simple")

# Initialize the Hunter API client
api_key = os.environ.get("HUNTER_API_KEY")
if not api_key:
    logger.error("HUNTER_API_KEY environment variable is not set")
    exit(1)

hunter_api = HunterAPI(api_key)

# Create the FastAPI app
app = FastAPI(title="Hunter MCP Simple Server", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define tools
@app.get("/tools/list")
async def list_tools():
    """List available tools for the Hunter API."""
    logger.info("Tools list requested")
    return {
        "tools": [
            {
                "name": "email_finder",
                "description": "Find the most likely email address from a domain name, first name, and last name",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "domain": {"type": "string", "description": "The domain name of the company (e.g., 'google.com')"},
                        "first_name": {"type": "string", "description": "The first name of the person"},
                        "last_name": {"type": "string", "description": "The last name of the person"}
                    },
                    "required": ["domain", "first_name", "last_name"]
                }
            },
            {
                "name": "domain_search",
                "description": "Find email addresses from a domain name",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "domain": {"type": "string", "description": "The domain name to search (e.g., 'google.com')"}
                    },
                    "required": ["domain"]
                }
            }
        ]
    }

@app.post("/tools/call")
async def call_tool(request: Request):
    """Handle tool execution."""
    try:
        data = await request.json()
        name = data.get("name")
        arguments = data.get("arguments", {})
        
        logger.info(f"Tool call: {name} with arguments {arguments}")
        
        if name == "email_finder":
            result = await hunter_api.find_email(**arguments)
            return {
                "content": [
                    {"type": "text", "text": json.dumps(result, indent=2)}
                ]
            }
        
        elif name == "domain_search":
            result = await hunter_api.domain_search(arguments["domain"])
            return {
                "content": [
                    {"type": "text", "text": json.dumps(result, indent=2)}
                ]
            }
        
        else:
            logger.error(f"Unknown tool: {name}")
            return JSONResponse(status_code=404, content={"error": f"Unknown tool: {name}"})
    
    except Exception as e:
        logger.error(f"Error executing tool: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# SSE endpoint for MCP
@app.get("/sse")
async def sse_endpoint(request: Request):
    """Server-Sent Events endpoint for MCP."""
    logger.info("SSE connection requested")
    
    async def event_generator():
        try:
            # Initial connection event
            logger.info("Sending connected event")
            yield {"event": "connected", "data": json.dumps({"server": "hunter-mcp-simple", "version": "1.0.0"})}
            await asyncio.sleep(0.1)
            
            # Send capabilities message
            logger.info("Sending capabilities event")
            yield {"event": "capabilities", "data": json.dumps({"tools": {"list": True, "call": True}})}
            
            # Keep connection alive
            while True:
                await asyncio.sleep(30)
                yield {"event": "ping", "data": json.dumps({"timestamp": asyncio.get_event_loop().time()})}
        except asyncio.CancelledError:
            logger.info("SSE connection was cancelled")
        except Exception as e:
            logger.error(f"Error in SSE event generator: {e}")
    
    return EventSourceResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Hunter MCP Simple Server is running", "version": "1.0.0"}

# Run the server
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting Hunter MCP Simple Server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
