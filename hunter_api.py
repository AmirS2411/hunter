#!/usr/bin/env python3
import aiohttp
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger("hunter-api")

class HunterAPI:
    """Client for the Hunter.io API."""
    
    BASE_URL = "https://api.hunter.io/v2"
    
    def __init__(self, api_key: str):
        """Initialize the Hunter API client.
        
        Args:
            api_key: Hunter API key
        """
        self.api_key = api_key
        self.session = None
    
    async def _ensure_session(self):
        """Ensure an aiohttp session exists."""
        if self.session is None:
            self.session = aiohttp.ClientSession()
    
    async def _request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a request to the Hunter API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Request parameters
            
        Returns:
            API response as a dictionary
        """
        await self._ensure_session()
        
        if params is None:
            params = {}
        
        # Add API key to parameters
        params["api_key"] = self.api_key
        
        url = f"{self.BASE_URL}/{endpoint}"
        logger.debug(f"Making {method} request to {url} with params {params}")
        
        try:
            async with self.session.request(method, url, params=params) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientResponseError as e:
            logger.error(f"API error: {e.status} - {e.message}")
            error_data = await response.json() if response.content_type == 'application/json' else {"error": e.message}
            raise ValueError(f"Hunter API error: {error_data.get('errors', [{'details': e.message}])[0].get('details')}")
        except aiohttp.ClientError as e:
            logger.error(f"Request error: {str(e)}")
            raise ValueError(f"Request error: {str(e)}")
    
    async def find_email(self, domain: str, first_name: Optional[str] = None, 
                        last_name: Optional[str] = None, company: Optional[str] = None,
                        full_name: Optional[str] = None) -> Dict[str, Any]:
        """Find the most likely email address from a domain name, first name, and last name.
        
        Args:
            domain: The domain name of the company
            first_name: The first name of the person
            last_name: The last name of the person
            company: Optional company name if domain is not provided
            full_name: Optional full name if first and last name are not provided separately
            
        Returns:
            Email finder result
        """
        params = {"domain": domain}
        
        if first_name:
            params["first_name"] = first_name
        if last_name:
            params["last_name"] = last_name
        if company:
            params["company"] = company
        if full_name:
            params["full_name"] = full_name
            
        response = await self._request("GET", "email-finder", params)
        return response.get("data", {})
    
    async def verify_email(self, email: str) -> Dict[str, Any]:
        """Verify the deliverability of an email address.
        
        Args:
            email: The email address to verify
            
        Returns:
            Email verification result
        """
        params = {"email": email}
        response = await self._request("GET", "email-verifier", params)
        return response.get("data", {})
    
    async def domain_search(self, domain: str, limit: int = 10, type: Optional[str] = None) -> Dict[str, Any]:
        """Find email addresses from a domain name.
        
        Args:
            domain: The domain name to search
            limit: Maximum number of results to return
            type: Type of emails to return (personal or generic)
            
        Returns:
            Domain search result
        """
        params = {
            "domain": domain,
            "limit": limit
        }
        
        if type:
            params["type"] = type
            
        response = await self._request("GET", "domain-search", params)
        return response.get("data", {})
