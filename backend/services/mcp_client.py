import json
import logging
from typing import Any, Dict, List, Optional

from backend.services.ai_service import AIService


class MCPClient:
    """Lightweight client for invoking our MCP tool."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._inprocess_tool = None
        try:
            from tools import mcp_server  # type: ignore

            if hasattr(mcp_server, "generate_itinerary"):
                self._inprocess_tool = mcp_server.generate_itinerary
                self.logger.info("MCP client using in-process tool.")
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.warning("Failed to import MCP server tool: %s", exc)

        self.ai_service = AIService()

    def generate_itinerary(
        self,
        city: str,
        days: int,
        preferences: Optional[List[str]] = None,
        pace: str = "中庸",
        transport_mode: str = "driving",
        priority: str = "效率优先",
    ) -> Dict[str, Any]:
        """Call MCP tool if available, otherwise fallback to POIService directly."""
        preferences = preferences or []

        if self._inprocess_tool:
            try:
                response = self._inprocess_tool(
                    city=city,
                    days=days,
                    preferences=",".join(preferences),
                    pace=pace,
                    transport_mode=transport_mode,
                    priority=priority,
                )
                if isinstance(response, str):
                    return json.loads(response)
                if isinstance(response, dict):
                    return response
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.warning("MCP tool invocation failed, fallback to POIService: %s", exc)

        return self.ai_service.generate_trip_plan(
            city=city,
            days=days,
            preferences=preferences,
            pace=pace,
            transport_mode=transport_mode,
            priority=priority,
        )

