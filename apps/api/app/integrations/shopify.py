from __future__ import annotations

import hashlib
import hmac
from urllib.parse import urlencode

import httpx

from app.core.errors import AppError, TransientUpstreamError
from app.core.settings import get_settings


class ShopifyClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def build_install_url(self, shop_domain: str, state: str, redirect_uri: str | None = None) -> str:
        redirect = redirect_uri or self.settings.shopify_redirect_url
        if not redirect or not self.settings.shopify_api_key:
            raise AppError(code="validation_error", message="Shopify app URL configuration is incomplete", status_code=422)
        query = urlencode(
            {
                "client_id": self.settings.shopify_api_key,
                "scope": self.settings.shopify_scopes,
                "redirect_uri": redirect,
                "state": state,
            }
        )
        return f"https://{shop_domain}/admin/oauth/authorize?{query}"

    def exchange_code_for_token(self, shop_domain: str, code: str) -> dict:
        if not self.settings.shopify_api_key or not self.settings.shopify_api_secret:
            raise AppError(code="validation_error", message="Shopify credentials are missing", status_code=422)
        payload = {
            "client_id": self.settings.shopify_api_key,
            "client_secret": self.settings.shopify_api_secret,
            "code": code,
        }
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(f"https://{shop_domain}/admin/oauth/access_token", json=payload)
        except httpx.HTTPError as exc:
            raise TransientUpstreamError("Shopify OAuth exchange failed due to a transient network error") from exc
        if response.status_code >= 400:
            raise AppError(code="upstream_error", message="Failed to exchange Shopify OAuth code", status_code=502, details=response.json())
        return response.json()

    def verify_hmac(self, params: dict[str, str], provided_hmac: str) -> bool:
        secret = self.settings.shopify_api_secret
        if not secret:
            return False
        filtered = {k: v for k, v in params.items() if k != "hmac"}
        message = "&".join(f"{k}={v}" for k, v in sorted(filtered.items()))
        digest = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(digest, provided_hmac)

    def graphql(self, shop_domain: str, access_token: str, query: str, variables: dict | None = None) -> dict:
        headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json",
        }
        payload = {"query": query, "variables": variables or {}}
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"https://{shop_domain}/admin/api/{self.settings.shopify_api_version}/graphql.json",
                    json=payload,
                    headers=headers,
                )
        except httpx.HTTPError as exc:
            raise TransientUpstreamError("Shopify request failed due to a transient network error") from exc
        if response.status_code >= 400:
            raise AppError(code="upstream_error", message="Shopify GraphQL request failed", status_code=502, details=response.json())
        body = response.json()
        if body.get("errors"):
            raise AppError(code="upstream_error", message="Shopify GraphQL response contains errors", status_code=502, details=body["errors"])
        return body["data"]

    def fetch_products(self, shop_domain: str, access_token: str) -> list[dict]:
        query = """
        query Products {
          products(first: 25) {
            nodes {
              id
              handle
              title
              descriptionHtml
              vendor
              productType
              tags
              status
              seo { title description }
              variants(first: 25) {
                nodes {
                  id
                  sku
                  title
                  price
                  compareAtPrice
                  inventoryQuantity
                }
              }
            }
          }
        }
        """
        data = self.graphql(shop_domain, access_token, query)
        results = []
        for node in data["products"]["nodes"]:
            results.append(
                {
                    "external_product_id": node["id"],
                    "handle": node["handle"],
                    "title": node["title"],
                    "description": node.get("descriptionHtml"),
                    "vendor": node.get("vendor"),
                    "category": node.get("productType"),
                    "tags": node.get("tags", []),
                    "seo_title": (node.get("seo") or {}).get("title"),
                    "seo_description": (node.get("seo") or {}).get("description"),
                    "status": (node.get("status") or "ACTIVE").lower(),
                    "variants": [
                        {
                            "external_variant_id": variant["id"],
                            "sku": variant.get("sku"),
                            "title": variant.get("title") or "",
                            "price": variant.get("price") or 0,
                            "compare_at_price": variant.get("compareAtPrice"),
                            "inventory_quantity": variant.get("inventoryQuantity") or 0,
                        }
                        for variant in node["variants"]["nodes"]
                    ],
                }
            )
        return results

    def fetch_orders(self, shop_domain: str, access_token: str) -> list[dict]:
        query = """
        query Orders {
          orders(first: 25, sortKey: CREATED_AT, reverse: true) {
            nodes {
              id
              displayFulfillmentStatus
              displayFinancialStatus
              createdAt
              currentSubtotalPriceSet { shopMoney { amount currencyCode } }
              currentTotalPriceSet { shopMoney { amount currencyCode } }
              customer { id email firstName lastName phone numberOfOrders amountSpent { amount } }
              lineItems(first: 25) {
                nodes {
                  id
                  sku
                  name
                  quantity
                  originalUnitPriceSet { shopMoney { amount } }
                }
              }
            }
          }
        }
        """
        data = self.graphql(shop_domain, access_token, query)
        results = []
        for node in data["orders"]["nodes"]:
            customer = node.get("customer")
            line_items = []
            for item in node["lineItems"]["nodes"]:
                unit_price = (item.get("originalUnitPriceSet") or {}).get("shopMoney", {}).get("amount") or 0
                line_items.append(
                    {
                        "external_line_item_id": item["id"],
                        "sku": item.get("sku"),
                        "title": item.get("name"),
                        "quantity": item.get("quantity", 0),
                        "unit_price": unit_price,
                        "total_price": float(unit_price) * item.get("quantity", 0),
                    }
                )
            results.append(
                {
                    "external_order_id": node["id"],
                    "status": "open",
                    "payment_status": (node.get("displayFinancialStatus") or "").lower(),
                    "fulfillment_status": (node.get("displayFulfillmentStatus") or "").lower(),
                    "subtotal": ((node.get("currentSubtotalPriceSet") or {}).get("shopMoney") or {}).get("amount") or 0,
                    "total": ((node.get("currentTotalPriceSet") or {}).get("shopMoney") or {}).get("amount") or 0,
                    "currency": ((node.get("currentTotalPriceSet") or {}).get("shopMoney") or {}).get("currencyCode"),
                    "customer": {
                        "external_customer_id": customer["id"],
                        "email": customer.get("email"),
                        "first_name": customer.get("firstName"),
                        "last_name": customer.get("lastName"),
                        "phone": customer.get("phone"),
                        "total_orders": customer.get("numberOfOrders", 0),
                        "total_spend": ((customer.get("amountSpent") or {}).get("amount")) or 0,
                    } if customer else None,
                    "items": line_items,
                }
            )
        return results

    def fetch_customers(self, shop_domain: str, access_token: str) -> list[dict]:
        query = """
        query Customers {
          customers(first: 25, sortKey: CREATED_AT, reverse: true) {
            nodes {
              id
              email
              firstName
              lastName
              phone
              numberOfOrders
              amountSpent { amount }
            }
          }
        }
        """
        data = self.graphql(shop_domain, access_token, query)
        return [
            {
                "external_customer_id": node["id"],
                "email": node.get("email"),
                "first_name": node.get("firstName"),
                "last_name": node.get("lastName"),
                "phone": node.get("phone"),
                "total_orders": node.get("numberOfOrders", 0),
                "total_spend": ((node.get("amountSpent") or {}).get("amount")) or 0,
            }
            for node in data["customers"]["nodes"]
        ]

    def publish_product_content(self, shop_domain: str, access_token: str, product_external_id: str, payload: dict) -> dict:
        query = """
        mutation UpdateProduct($input: ProductInput!) {
          productUpdate(product: $input) {
            product { id title handle }
            userErrors { field message }
          }
        }
        """
        variables = {
            "input": {
                "id": product_external_id,
                "title": payload.get("generated_title"),
                "descriptionHtml": payload.get("generated_description"),
                "tags": payload.get("generated_tags"),
                "seo": {
                    "title": payload.get("generated_seo_title"),
                    "description": payload.get("generated_seo_description"),
                },
            }
        }
        data = self.graphql(shop_domain, access_token, query, variables=variables)
        errors = data["productUpdate"].get("userErrors") or []
        if errors:
            raise AppError(code="upstream_error", message="Shopify publish returned user errors", status_code=502, details={"errors": errors})
        return data["productUpdate"]["product"]
