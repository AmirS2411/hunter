# Hunter MCP - Email Scraper MCP Server

A Model Context Protocol (MCP) server for Hunter.io's email scraping capabilities, designed to integrate with Shortwave and other MCP-compatible clients.

## Overview

This MCP server provides a bridge between Hunter.io's email finding API and MCP-compatible clients like Shortwave. It allows you to search for email addresses from websites and domains using natural language queries through your MCP-compatible client.

## Features

- **Email Finder**: Find the most likely email address for a person at a specific company
- **Email Verification**: Verify the deliverability of an email address
- **Domain Search**: Find email addresses associated with a domain

## Requirements

- Python 3.8+
- Hunter.io API key (get one at [hunter.io](https://hunter.io/users/sign_up?from=api))

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/hunter-mcp.git
   cd hunter-mcp
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set your Hunter API key as an environment variable:
   ```
   export HUNTER_API_KEY="your_api_key_here"
   ```

## Usage

### Running the MCP Server

Run the server with:

```
python main.py
```

### Integrating with Shortwave

To integrate with Shortwave:

#### Local MCP Server (Desktop App)

1. Go to the [AI integrations](https://app.shortwave.com/settings/integrations) page in the Shortwave app
2. Click on "Add custom integration"
3. Select "Local MCP server"
4. Give your server a name (e.g., "Hunter Email Finder")
5. Provide the command and arguments:
   - Command: `python` or the path to your Python executable
   - Arguments: `/path/to/hunter-mcp/main.py`
   - Environment Variables: `HUNTER_API_KEY=your_api_key_here`
6. Click "Save"
7. Toggle the switch to enable the server

#### Remote MCP Server

If you're hosting the MCP server remotely with an SSE endpoint:

1. Go to the [AI integrations](https://app.shortwave.com/settings/integrations) page in the Shortwave app
2. Click on "Add custom integration"
3. Select "Remote MCP server"
4. Give your server a name (e.g., "Hunter Email Finder")
5. Enter the URL of your MCP server's SSE endpoint
6. Click "Save"
7. Toggle the switch to enable the server

## Example Queries

Once integrated with your MCP client, you can use natural language to interact with the Hunter API:

- "Find the email address for John Smith at google.com"
- "Verify if john.smith@google.com is a valid email"
- "Search for email addresses from microsoft.com"
- "Find emails from the marketing team at apple.com"

## Configuration

You can configure the server by modifying the `main.py` file or by setting environment variables:

- `HUNTER_API_KEY`: Your Hunter.io API key (required)
- `LOG_LEVEL`: Logging level (default: INFO)

## Development

### Project Structure

- `main.py`: Main MCP server implementation
- `hunter_api.py`: Hunter API client
- `requirements.txt`: Python dependencies

### Adding New Features

To add new Hunter API features:

1. Add the API method to `hunter_api.py`
2. Add a new tool definition in the `list_tools()` function in `main.py`
3. Add the tool implementation in the `call_tool()` function in `main.py`

## License

MIT

## Acknowledgements

- [Hunter.io](https://hunter.io/) for their email finding API
- [Model Context Protocol](https://modelcontextprotocol.io/) for the MCP specification
- [Shortwave](https://www.shortwave.com/) for their MCP integration
