from io import BytesIO
import json
from typing import Optional, Dict

import bpy
import requests
from PIL import Image


def get_backend_url() -> str:
    """Get the current backend URL with validation and normalization"""
    try:
        backend_props = bpy.context.scene.backend_properties
        url = backend_props.url

        # Validate and normalize URL
        if not url or url.strip() == "":
            url = "http://127.0.0.1:8188"
        elif not url.startswith(("http://", "https://")):
            url = f"http://{url}"

        return url
    except Exception as e:
        print(f"Error getting backend URL: {e}")
        return "http://127.0.0.1:8188"  # fallback


def backend_request(
    endpoint: str,
    method: str = "GET",
    params: Optional[Dict] = None,
    data: Optional[Dict] = None,
    json_data: Optional[Dict] = None,
    files: Optional[Dict] = None,
    timeout: int = 15,
) -> Optional[requests.Response]:
    """
    Unified function for all backend API calls

    Args:
        endpoint: API endpoint (e.g., "/view", "/prompt", "/upload/image")
        method: HTTP method ("GET", "POST", etc.)
        params: URL parameters
        data: Form data
        json_data: JSON data (will be encoded automatically)
        files: Files for upload
        timeout: Request timeout in seconds

    Returns:
        Response object or None if failed
    """
    base_url = get_backend_url()
    url = f"{base_url}{endpoint}"

    try:
        print(f"Backend request: {method} {url}")
        if params:
            print(f"   Params: {params}")

        # Prepare request arguments - use a dict that can hold any type
        kwargs = {}

        # Add timeout (always present)
        kwargs["timeout"] = timeout

        # Add optional parameters only if they have values
        if params:
            kwargs["params"] = params
        if data:
            kwargs["data"] = data
        if files:
            kwargs["files"] = files

        # Handle JSON data
        if json_data:
            kwargs["data"] = json.dumps(json_data).encode("utf-8")
            kwargs["headers"] = {"Content-Type": "application/json"}

        print(f"   Request kwargs keys: {list(kwargs.keys())}")

        # Make request
        if method.upper() == "GET":
            response = requests.get(url, **kwargs)
        elif method.upper() == "POST":
            response = requests.post(url, **kwargs)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        print(f"Response: {response.status_code}")
        return response

    except Exception as e:
        print(f"Backend request failed - URL: {url}, Error: {e}")
        return None


def convert_to_bytes(image: Image.Image):

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer


# pyright: reportAttributeAccessIssue=false


def send_image_function(scene: bpy.types.Scene, image_name: str, image: Image.Image):
    """Send the image to the comfyUI backend"""

    # Send Image
    buffer = convert_to_bytes(image)
    files = {"image": (image_name, buffer, "image/png")}

    data = {
        "type": "input",
        "overwrite": "true",
    }

    response = backend_request("/upload/image", method="POST", files=files, data=data)

    return response.status_code if response else 500
