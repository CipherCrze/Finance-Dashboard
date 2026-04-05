"""
Standalone ReDoc server that serves the API documentation
on a separate port (8001) using a self-contained HTML page.

Usage:
    python redoc_server.py
"""

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

redoc_app = FastAPI(title="ReDoc Server")

redoc_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

REDOC_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Finance Dashboard API - ReDoc</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { margin: 0; padding: 0; font-family: sans-serif; }
    </style>
</head>
<body>
    <div id="redoc-container"></div>
    <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
    <script>
        Redoc.init('http://localhost:8000/openapi.json', {
            scrollYOffset: 0,
            hideDownloadButton: false,
            theme: {
                colors: {
                    primary: { main: '#6366f1' }
                },
                typography: {
                    fontSize: '15px',
                    fontFamily: 'system-ui, -apple-system, sans-serif',
                    headings: { fontFamily: 'system-ui, -apple-system, sans-serif' }
                },
                sidebar: {
                    backgroundColor: '#1e1b4b',
                    textColor: '#e0e7ff',
                    activeTextColor: '#a5b4fc'
                },
                rightPanel: {
                    backgroundColor: '#1e293b'
                }
            }
        }, document.getElementById('redoc-container'));
    </script>
</body>
</html>
"""


@redoc_app.get("/", response_class=HTMLResponse)
async def serve_redoc():
    """Serve the ReDoc documentation page."""
    return REDOC_HTML


@redoc_app.get("/health")
async def health():
    return {"status": "redoc server running", "api_docs": "http://localhost:8001"}


if __name__ == "__main__":
    print("ReDoc server starting on http://localhost:8001")
    print("Make sure the main API is running on http://localhost:8000")
    uvicorn.run(redoc_app, host="127.0.0.1", port=8001)
