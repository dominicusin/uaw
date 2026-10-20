"""
Wix Adapter for UAW
Адаптер для работы с Wix через REST API
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum
import aiohttp
import json

from .base import BaseAdapter, AdapterConfig, AdapterResult, AdapterStatus


class WixConfig(AdapterConfig):
    """Configuration for Wix adapter"""
    
    def __init__(self):
        super().__init__(
            name="wix",
            display_name="Wix",
            description="Wix adapter for website management, CMS, and e-commerce",
            base_url="https://api.wix.com/v1",
            api_version="v1",
            timeout=30,
            max_retries=3,
            rate_limit=100,  # Wix API rate limit per minute
            auth_method="oauth2",
            requires_auth=True,
            supports_read=True,
            supports_write=True,
            supports_webhooks=True,
            icon_url="https://www.wix.com/favicon.ico"
        )
        self._capabilities = [
            # Site operations
            {
                "name": "list_sites",
                "description": "List all sites",
                "operation": "read",
                "parameters": ["limit", "cursor", "query"],
                "returns": "List of sites"
            },
            {
                "name": "get_site",
                "description": "Get site details",
                "operation": "read",
                "parameters": ["site_id", "fields"],
                "returns": "Site details"
            },
            {
                "name": "create_site",
                "description": "Create a new site",
                "operation": "write",
                "parameters": ["name", "template_id", "language", "timezone"],
                "returns": "Created site"
            },
            {
                "name": "update_site",
                "description": "Update a site",
                "operation": "write",
                "parameters": ["site_id", "name", "description", "settings"],
                "returns": "Updated site"
            },
            {
                "name": "delete_site",
                "description": "Delete a site",
                "operation": "delete",
                "parameters": ["site_id"],
                "returns": "Success status"
            },
            {
                "name": "publish_site",
                "description": "Publish a site",
                "operation": "write",
                "parameters": ["site_id", "publish_settings"],
                "returns": "Published site"
            },
            {
                "name": "unpublish_site",
                "description": "Unpublish a site",
                "operation": "write",
                "parameters": ["site_id"],
                "returns": "Unpublished site"
            },
            # Page operations
            {
                "name": "list_pages",
                "description": "List pages in a site",
                "operation": "read",
                "parameters": ["site_id", "limit", "cursor"],
                "returns": "List of pages"
            },
            {
                "name": "get_page",
                "description": "Get page details",
                "operation": "read",
                "parameters": ["site_id", "page_id"],
                "returns": "Page details"
            },
            {
                "name": "create_page",
                "description": "Create a new page",
                "operation": "write",
                "parameters": ["site_id", "title", "page_type", "parent_page_id"],
                "returns": "Created page"
            },
            {
                "name": "update_page",
                "description": "Update a page",
                "operation": "write",
                "parameters": ["site_id", "page_id", "title", "content", "settings"],
                "returns": "Updated page"
            },
            {
                "name": "delete_page",
                "description": "Delete a page",
                "operation": "delete",
                "parameters": ["site_id", "page_id"],
                "returns": "Success status"
            },
            {
                "name": "reorder_pages",
                "description": "Reorder pages",
                "operation": "write",
                "parameters": ["site_id", "page_order"],
                "returns": "Reordered pages"
            },
            # CMS operations
            {
                "name": "list_collections",
                "description": "List CMS collections",
                "operation": "read",
                "parameters": ["site_id", "limit", "cursor"],
                "returns": "List of collections"
            },
            {
                "name": "get_collection",
                "description": "Get collection details",
                "operation": "read",
                "parameters": ["site_id", "collection_id"],
                "returns": "Collection details"
            },
            {
                "name": "create_collection",
                "description": "Create a new collection",
                "operation": "write",
                "parameters": ["site_id", "name", "fields", "settings"],
                "returns": "Created collection"
            },
            {
                "name": "update_collection",
                "description": "Update a collection",
                "operation": "write",
                "parameters": ["site_id", "collection_id", "name", "fields", "settings"],
                "returns": "Updated collection"
            },
            {
                "name": "delete_collection",
                "description": "Delete a collection",
                "operation": "delete",
                "parameters": ["site_id", "collection_id"],
                "returns": "Success status"
            },
            # CMS Items
            {
                "name": "list_items",
                "description": "List items in a collection",
                "operation": "read",
                "parameters": ["site_id", "collection_id", "limit", "cursor", "query"],
                "returns": "List of items"
            },
            {
                "name": "get_item",
                "description": "Get item details",
                "operation": "read",
                "parameters": ["site_id", "collection_id", "item_id"],
                "returns": "Item details"
            },
            {
                "name": "create_item",
                "description": "Create a new item",
                "operation": "write",
                "parameters": ["site_id", "collection_id", "data"],
                "returns": "Created item"
            },
            {
                "name": "update_item",
                "description": "Update an item",
                "operation": "write",
                "parameters": ["site_id", "collection_id", "item_id", "data"],
                "returns": "Updated item"
            },
            {
                "name": "delete_item",
                "description": "Delete an item",
                "operation": "delete",
                "parameters": ["site_id", "collection_id", "item_id"],
                "returns": "Success status"
            },
            # Media operations
            {
                "name": "list_media",
                "description": "List media items",
                "operation": "read",
                "parameters": ["site_id", "limit", "cursor", "media_type"],
                "returns": "List of media items"
            },
            {
                "name": "get_media",
                "description": "Get media details",
                "operation": "read",
                "parameters": ["site_id", "media_id"],
                "returns": "Media details"
            },
            {
                "name": "upload_media",
                "description": "Upload a media file",
                "operation": "write",
                "parameters": ["site_id", "file_data", "media_type"],
                "returns": "Uploaded media"
            },
            {
                "name": "delete_media",
                "description": "Delete a media item",
                "operation": "delete",
                "parameters": ["site_id", "media_id"],
                "returns": "Success status"
            },
            # E-commerce operations
            {
                "name": "list_products",
                "description": "List products",
                "operation": "read",
                "parameters": ["site_id", "limit", "cursor", "query"],
                "returns": "List of products"
            },
            {
                "name": "get_product",
                "description": "Get product details",
                "operation": "read",
                "parameters": ["site_id", "product_id"],
                "returns": "Product details"
            },
            {
                "name": "create_product",
                "description": "Create a new product",
                "operation": "write",
                "parameters": ["site_id", "name", "price", "description", "images", "options"],
                "returns": "Created product"
            },
            {
                "name": "update_product",
                "description": "Update a product",
                "operation": "write",
                "parameters": ["site_id", "product_id", "name", "price", "description", "images", "options"],
                "returns": "Updated product"
            },
            {
                "name": "delete_product",
                "description": "Delete a product",
                "operation": "delete",
                "parameters": ["site_id", "product_id"],
                "returns": "Success status"
            },
            # Order operations
            {
                "name": "list_orders",
                "description": "List orders",
                "operation": "read",
                "parameters": ["site_id", "limit", "cursor", "status", "date_from", "date_to"],
                "returns": "List of orders"
            },
            {
                "name": "get_order",
                "description": "Get order details",
                "operation": "read",
                "parameters": ["site_id", "order_id"],
                "returns": "Order details"
            },
            {
                "name": "update_order",
                "description": "Update an order",
                "operation": "write",
                "parameters": ["site_id", "order_id", "status", "notes"],
                "returns": "Updated order"
            },
            # Customer operations
            {
                "name": "list_customers",
                "description": "List customers",
                "operation": "read",
                "parameters": ["site_id", "limit", "cursor", "query"],
                "returns": "List of customers"
            },
            {
                "name": "get_customer",
                "description": "Get customer details",
                "operation": "read",
                "parameters": ["site_id", "customer_id"],
                "returns": "Customer details"
            },
            {
                "name": "create_customer",
                "description": "Create a new customer",
                "operation": "write",
                "parameters": ["site_id", "first_name", "last_name", "email", "phone", "address"],
                "returns": "Created customer"
            },
            {
                "name": "update_customer",
                "description": "Update a customer",
                "operation": "write",
                "parameters": ["site_id", "customer_id", "first_name", "last_name", "email", "phone", "address"],
                "returns": "Updated customer"
            },
            # Domain operations
            {
                "name": "list_domains",
                "description": "List domains",
                "operation": "read",
                "parameters": ["site_id", "limit", "cursor"],
                "returns": "List of domains"
            },
            {
                "name": "get_domain",
                "description": "Get domain details",
                "operation": "read",
                "parameters": ["site_id", "domain_id"],
                "returns": "Domain details"
            },
            {
                "name": "connect_domain",
                "description": "Connect a domain",
                "operation": "write",
                "parameters": ["site_id", "domain_name", "dns_settings"],
                "returns": "Connected domain"
            },
            {
                "name": "disconnect_domain",
                "description": "Disconnect a domain",
                "operation": "write",
                "parameters": ["site_id", "domain_id"],
                "returns": "Disconnected domain"
            },
            # Analytics operations
            {
                "name": "get_analytics",
                "description": "Get site analytics",
                "operation": "read",
                "parameters": ["site_id", "date_from", "date_to", "metrics"],
                "returns": "Analytics data"
            },
            {
                "name": "get_visitors",
                "description": "Get visitor statistics",
                "operation": "read",
                "parameters": ["site_id", "date_from", "date_to", "group_by"],
                "returns": "Visitor statistics"
            },
            # Form operations
            {
                "name": "list_forms",
                "description": "List forms",
                "operation": "read",
                "parameters": ["site_id", "limit", "cursor"],
                "returns": "List of forms"
            },
            {
                "name": "get_form",
                "description": "Get form details",
                "operation": "read",
                "parameters": ["site_id", "form_id"],
                "returns": "Form details"
            },
            {
                "name": "get_form_submissions",
                "description": "Get form submissions",
                "operation": "read",
                "parameters": ["site_id", "form_id", "limit", "cursor", "date_from", "date_to"],
                "returns": "List of submissions"
            },
            # Booking operations
            {
                "name": "list_services",
                "description": "List booking services",
                "operation": "read",
                "parameters": ["site_id", "limit", "cursor"],
                "returns": "List of services"
            },
            {
                "name": "list_bookings",
                "description": "List bookings",
                "operation": "read",
                "parameters": ["site_id", "limit", "cursor", "date_from", "date_to", "status"],
                "returns": "List of bookings"
            },
            {
                "name": "get_booking",
                "description": "Get booking details",
                "operation": "read",
                "parameters": ["site_id", "booking_id"],
                "returns": "Booking details"
            },
            # User operations
            {
                "name": "get_me",
                "description": "Get current user details",
                "operation": "read",
                "parameters": [],
                "returns": "Current user details"
            },
            {
                "name": "list_users",
                "description": "List users with access to sites",
                "operation": "read",
                "parameters": ["limit", "cursor"],
                "returns": "List of users"
            },
            # Webhook operations
            {
                "name": "list_webhooks",
                "description": "List webhooks",
                "operation": "read",
                "parameters": ["site_id", "limit", "cursor"],
                "returns": "List of webhooks"
            },
            {
                "name": "create_webhook",
                "description": "Create a webhook",
                "operation": "write",
                "parameters": ["site_id", "url", "events", "config"],
                "returns": "Created webhook"
            },
            {
                "name": "delete_webhook",
                "description": "Delete a webhook",
                "operation": "delete",
                "parameters": ["site_id", "webhook_id"],
                "returns": "Success status"
            },
        ]


class WixAdapter(BaseAdapter):
    """
    Wix adapter implementation.
    Uses REST API for Wix operations.
    """
    
    def __init__(self, config: Optional[WixConfig] = None):
        self.config = config or WixConfig()
        super().__init__(self.config)
        self.status = AdapterStatus.UNAVAILABLE
        
        # Action to endpoint mapping
        self.action_mappings = {
            # Site operations
            "list_sites": ("GET", "/sites"),
            "get_site": ("GET", "/sites/{site_id}"),
            "create_site": ("POST", "/sites"),
            "update_site": ("PUT", "/sites/{site_id}"),
            "delete_site": ("DELETE", "/sites/{site_id}"),
            "publish_site": ("POST", "/sites/{site_id}/publish"),
            "unpublish_site": ("POST", "/sites/{site_id}/unpublish"),
            
            # Page operations
            "list_pages": ("GET", "/sites/{site_id}/pages"),
            "get_page": ("GET", "/sites/{site_id}/pages/{page_id}"),
            "create_page": ("POST", "/sites/{site_id}/pages"),
            "update_page": ("PUT", "/sites/{site_id}/pages/{page_id}"),
            "delete_page": ("DELETE", "/sites/{site_id}/pages/{page_id}"),
            "reorder_pages": ("PUT", "/sites/{site_id}/pages/reorder"),
            
            # CMS operations
            "list_collections": ("GET", "/sites/{site_id}/cms/collections"),
            "get_collection": ("GET", "/sites/{site_id}/cms/collections/{collection_id}"),
            "create_collection": ("POST", "/sites/{site_id}/cms/collections"),
            "update_collection": ("PUT", "/sites/{site_id}/cms/collections/{collection_id}"),
            "delete_collection": ("DELETE", "/sites/{site_id}/cms/collections/{collection_id}"),
            
            # CMS Items
            "list_items": ("GET", "/sites/{site_id}/cms/collections/{collection_id}/items"),
            "get_item": ("GET", "/sites/{site_id}/cms/collections/{collection_id}/items/{item_id}"),
            "create_item": ("POST", "/sites/{site_id}/cms/collections/{collection_id}/items"),
            "update_item": ("PUT", "/sites/{site_id}/cms/collections/{collection_id}/items/{item_id}"),
            "delete_item": ("DELETE", "/sites/{site_id}/cms/collections/{collection_id}/items/{item_id}"),
            
            # Media operations
            "list_media": ("GET", "/sites/{site_id}/media"),
            "get_media": ("GET", "/sites/{site_id}/media/{media_id}"),
            "upload_media": ("POST", "/sites/{site_id}/media"),
            "delete_media": ("DELETE", "/sites/{site_id}/media/{media_id}"),
            
            # E-commerce operations
            "list_products": ("GET", "/sites/{site_id}/ecommerce/products"),
            "get_product": ("GET", "/sites/{site_id}/ecommerce/products/{product_id}"),
            "create_product": ("POST", "/sites/{site_id}/ecommerce/products"),
            "update_product": ("PUT", "/sites/{site_id}/ecommerce/products/{product_id}"),
            "delete_product": ("DELETE", "/sites/{site_id}/ecommerce/products/{product_id}"),
            
            # Order operations
            "list_orders": ("GET", "/sites/{site_id}/ecommerce/orders"),
            "get_order": ("GET", "/sites/{site_id}/ecommerce/orders/{order_id}"),
            "update_order": ("PUT", "/sites/{site_id}/ecommerce/orders/{order_id}"),
            
            # Customer operations
            "list_customers": ("GET", "/sites/{site_id}/ecommerce/customers"),
            "get_customer": ("GET", "/sites/{site_id}/ecommerce/customers/{customer_id}"),
            "create_customer": ("POST", "/sites/{site_id}/ecommerce/customers"),
            "update_customer": ("PUT", "/sites/{site_id}/ecommerce/customers/{customer_id}"),
            
            # Domain operations
            "list_domains": ("GET", "/sites/{site_id}/domains"),
            "get_domain": ("GET", "/sites/{site_id}/domains/{domain_id}"),
            "connect_domain": ("POST", "/sites/{site_id}/domains"),
            "disconnect_domain": ("DELETE", "/sites/{site_id}/domains/{domain_id}"),
            
            # Analytics operations
            "get_analytics": ("GET", "/sites/{site_id}/analytics"),
            "get_visitors": ("GET", "/sites/{site_id}/analytics/visitors"),
            
            # Form operations
            "list_forms": ("GET", "/sites/{site_id}/forms"),
            "get_form": ("GET", "/sites/{site_id}/forms/{form_id}"),
            "get_form_submissions": ("GET", "/sites/{site_id}/forms/{form_id}/submissions"),
            
            # Booking operations
            "list_services": ("GET", "/sites/{site_id}/bookings/services"),
            "list_bookings": ("GET", "/sites/{site_id}/bookings"),
            "get_booking": ("GET", "/sites/{site_id}/bookings/{booking_id}"),
            
            # User operations
            "get_me": ("GET", "/user"),
            "list_users": ("GET", "/users"),
            
            # Webhook operations
            "list_webhooks": ("GET", "/sites/{site_id}/webhooks"),
            "create_webhook": ("POST", "/sites/{site_id}/webhooks"),
            "delete_webhook": ("DELETE", "/sites/{site_id}/webhooks/{webhook_id}"),
        }
    
    async def initialize(self) -> bool:
        """Initialize Wix adapter"""
        try:
            # Test connection
            result = await self._make_request(
                method="GET",
                endpoint="/user"
            )
            if result.get("success", False):
                self.status = AdapterStatus.AVAILABLE
                return True
            else:
                self.status = AdapterStatus.UNAUTHORISED
                return False
        except Exception as e:
            self.last_error = str(e)
            self.status = AdapterStatus.ERROR
            return False
    
    async def check_status(self) -> AdapterStatus:
        """Check current status"""
        return self.status
    
    async def execute(
        self,
        action: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> AdapterResult:
        """
        Execute a Wix action.
        
        Args:
            action: Action to execute
            parameters: Action parameters
            
        Returns:
            AdapterResult with success status and data
        """
        if parameters is None:
            parameters = {}
        
        # Check if we're authenticated
        if self.status == AdapterStatus.UNAUTHORISED:
            return AdapterResult(
                success=False,
                error="Wix adapter requires authentication",
                status_code=401
            )
        
        # Check if action is supported
        if action not in self.action_mappings:
            return AdapterResult(
                success=False,
                error=f"Action '{action}' is not supported by Wix adapter",
                status_code=400
            )
        
        # Check rate limit
        if not await self.check_rate_limit():
            return AdapterResult(
                success=False,
                error="Rate limit exceeded",
                status_code=429
            )
        
        try:
            # Get HTTP method and endpoint
            method, endpoint = self.action_mappings[action]
            
            # Format endpoint with parameters
            formatted_endpoint = self._format_endpoint(endpoint, parameters)
            
            # Prepare request data
            request_data = self._prepare_request_data(action, parameters)
            
            # Make request
            result = await self._make_request(
                method=method,
                endpoint=formatted_endpoint,
                json_data=request_data.get("json"),
                data=request_data.get("data"),
                headers=request_data.get("headers", {})
            )
            
            return AdapterResult(
                success=result.get("success", True),
                data=result.get("data"),
                error=result.get("error"),
                status_code=result.get("status_code", 200),
                metadata=result.get("metadata")
            )
        except Exception as e:
            return AdapterResult(
                success=False,
                error=str(e),
                status_code=500
            )
    
    def _format_endpoint(self, endpoint: str, parameters: Dict[str, Any]) -> str:
        """Format endpoint with path parameters"""
        # Replace {param} with actual values
        for key, value in parameters.items():
            if isinstance(value, str):
                endpoint = endpoint.replace(f"{{{key}}}", value)
        return endpoint
    
    def _prepare_request_data(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare request data based on action"""
        request_data = {}
        
        # Remove path parameters from request data
        clean_params = {k: v for k, v in parameters.items() if not isinstance(v, str) or "{" not in v}
        
        # For POST, PUT, PATCH requests
        if action in ["create_site", "update_site", "create_page", "update_page",
                      "reorder_pages", "create_collection", "update_collection",
                      "create_item", "update_item", "upload_media", "create_product",
                      "update_product", "connect_domain", "publish_site",
                      "create_customer", "update_customer", "update_order",
                      "create_comment", "create_webhook", "create_form"]:
            request_data["json"] = clean_params
        
        # For GET requests with query parameters
        elif action in ["list_sites", "get_site", "list_pages", "get_page",
                        "list_collections", "get_collection", "list_items", "get_item",
                        "list_media", "get_media", "list_products", "get_product",
                        "list_orders", "get_order", "list_customers", "get_customer",
                        "list_domains", "get_domain", "get_analytics", "get_visitors",
                        "list_forms", "get_form", "get_form_submissions",
                        "list_services", "list_bookings", "get_booking",
                        "list_users", "get_me", "list_webhooks"]:
            request_data["params"] = clean_params
        
        # For file upload
        if action == "upload_media":
            request_data["data"] = clean_params
        
        return request_data
    
    # Convenience methods for common operations
    
    async def list_sites(self, limit: int = 100) -> AdapterResult:
        """List all sites"""
        return await self.execute("list_sites", {"limit": limit})
    
    async def get_site(self, site_id: str) -> AdapterResult:
        """Get site details"""
        return await self.execute("get_site", {"site_id": site_id})
    
    async def list_pages(self, site_id: str, limit: int = 100) -> AdapterResult:
        """List pages in a site"""
        return await self.execute("list_pages", {
            "site_id": site_id,
            "limit": limit
        })
    
    async def create_page(
        self,
        site_id: str,
        title: str,
        page_type: str = "standard",
        parent_page_id: Optional[str] = None
    ) -> AdapterResult:
        """Create a new page"""
        params = {
            "site_id": site_id,
            "title": title,
            "page_type": page_type
        }
        if parent_page_id:
            params["parent_page_id"] = parent_page_id
        return await self.execute("create_page", params)
    
    async def update_page(
        self,
        site_id: str,
        page_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> AdapterResult:
        """Update a page"""
        params = {"site_id": site_id, "page_id": page_id}
        if title:
            params["title"] = title
        if content:
            params["content"] = content
        if settings:
            params["settings"] = settings
        return await self.execute("update_page", params)
    
    async def list_collections(self, site_id: str, limit: int = 100) -> AdapterResult:
        """List CMS collections"""
        return await self.execute("list_collections", {
            "site_id": site_id,
            "limit": limit
        })
    
    async def create_collection(
        self,
        site_id: str,
        name: str,
        fields: List[Dict[str, Any]],
        settings: Optional[Dict[str, Any]] = None
    ) -> AdapterResult:
        """Create a new collection"""
        params = {
            "site_id": site_id,
            "name": name,
            "fields": fields
        }
        if settings:
            params["settings"] = settings
        return await self.execute("create_collection", params)
    
    async def list_products(self, site_id: str, limit: int = 100) -> AdapterResult:
        """List products"""
        return await self.execute("list_products", {
            "site_id": site_id,
            "limit": limit
        })
    
    async def create_product(
        self,
        site_id: str,
        name: str,
        price: float,
        description: Optional[str] = None,
        images: Optional[List[str]] = None,
        options: Optional[List[Dict[str, Any]]] = None
    ) -> AdapterResult:
        """Create a new product"""
        params = {
            "site_id": site_id,
            "name": name,
            "price": price
        }
        if description:
            params["description"] = description
        if images:
            params["images"] = images
        if options:
            params["options"] = options
        return await self.execute("create_product", params)
    
    async def get_analytics(
        self,
        site_id: str,
        date_from: str,
        date_to: str,
        metrics: Optional[List[str]] = None
    ) -> AdapterResult:
        """Get site analytics"""
        params = {
            "site_id": site_id,
            "date_from": date_from,
            "date_to": date_to
        }
        if metrics:
            params["metrics"] = metrics
        return await self.execute("get_analytics", params)
    
    async def get_me(self) -> AdapterResult:
        """Get current user details"""
        return await self.execute("get_me", {})


# Singleton instance
wix_adapter = WixAdapter()
