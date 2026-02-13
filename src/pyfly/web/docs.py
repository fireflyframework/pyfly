"""Swagger UI and ReDoc HTML endpoint handlers."""

from __future__ import annotations

from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse

SWAGGER_UI_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title} - Swagger UI</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
        SwaggerUIBundle({{
            url: "{openapi_url}",
            dom_id: '#swagger-ui',
            presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
            layout: "StandaloneLayout"
        }})
    </script>
</body>
</html>"""

REDOC_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title} - ReDoc</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
</head>
<body>
    <redoc spec-url="{openapi_url}"></redoc>
    <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
</body>
</html>"""


def make_openapi_endpoint(spec_dict: dict):
    """Create the /openapi.json endpoint handler."""

    async def openapi_json(request: Request) -> JSONResponse:
        return JSONResponse(spec_dict)

    return openapi_json


def make_swagger_ui_endpoint(title: str, openapi_url: str = "/openapi.json"):
    """Create the /docs endpoint handler."""

    async def swagger_ui(request: Request) -> HTMLResponse:
        html = SWAGGER_UI_HTML.format(title=title, openapi_url=openapi_url)
        return HTMLResponse(html)

    return swagger_ui


def make_redoc_endpoint(title: str, openapi_url: str = "/openapi.json"):
    """Create the /redoc endpoint handler."""

    async def redoc(request: Request) -> HTMLResponse:
        html = REDOC_HTML.format(title=title, openapi_url=openapi_url)
        return HTMLResponse(html)

    return redoc
