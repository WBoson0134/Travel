#!/usr/bin/env python3
"""MCP server exposing travel-planner tools.

Usage::

    PYTHONPATH=. python tools/mcp_server.py

This starts a Model Context Protocol (MCP) server named ``travel-mcp`` with
one tool called ``generate_itinerary``.  The tool delegates to the existing
``POIService`` so the model can request draft itineraries without needing to
know about our internal APIs.  The server keeps all API keys on the backend
side; the model只 sees structured JSON results.

To use with Claude Desktop for example, add this snippet to
``claude_desktop_config.json``::

    "mcpServers": {
      "travel-mcp": {
        "command": "python",
        "args": ["/absolute/path/to/tools/mcp_server.py"]
      }
    }

Restart Claude and在聊天里指示 “调用 generate_itinerary(city='北京', days=3)”。

Requires ``model-context-protocol`` >= 0.1.0.
"""
from __future__ import annotations

import json
import logging
from typing import List


try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:
    raise ImportError(
        'model-context-protocol package not found. Install via '
        '"pip install git+https://github.com/modelcontextprotocol/python.git#egg=model-context-protocol"'
    ) from exc

from backend.services.ai_service import AIService

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

server = FastMCP("travel-mcp")
ai_service = AIService()


def _parse_preferences(preferences: str | List[str] | None) -> List[str]:
    if preferences is None:
        return []
    if isinstance(preferences, list):
        return [p.strip() for p in preferences if isinstance(p, str) and p.strip()]
    return [p.strip() for p in str(preferences).split(',') if p.strip()]


@server.tool()
async def generate_itinerary(
    city: str,
    days: int,
    preferences: str | List[str] | None = None,
    pace: str = "中庸",
    transport_mode: str = "driving",
    priority: str = "效率优先",
) -> str:
    """Generate an itinerary using the full AI service.

    Parameters
    ----------
    city: str
        Destination city (必填).
    days: int
        Trip duration in days.
    preferences: str | list[str]
        兴趣偏好, either comma separated string or list.
    pace: str
        节奏 (佛系/中庸/硬核).
    transport_mode: str
        交通方式 (driving/walking/transit/bicycling).

    Returns
    -------
    str
        JSON string describing the itinerary.
    """
    logger.info("MCP tool generate_itinerary called: city=%s, days=%s", city, days)
    pref_list = _parse_preferences(preferences)
    itinerary = ai_service.generate_trip_plan(
        city=city,
        days=int(days),
        preferences=pref_list,
        pace=pace,
        transport_mode=transport_mode,
        priority=priority,
    )
    return json.dumps(itinerary, ensure_ascii=False)


if __name__ == "__main__":
    logger.info("Starting MCP server 'travel-mcp'")
    server.run()
