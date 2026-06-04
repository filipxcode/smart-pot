import logging
from typing import Literal

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.usage import UsageLimits

from agent.model import build_model
from agent.prompts.prompts import PromptsOrganizer
from config.settings import get_settings

logger = logging.getLogger(__name__)


_ROUTER_LIMITS = UsageLimits(request_limit=3)


class RouterDecision(BaseModel):
    decision: Literal["tool", "reject"]


_route_agent = Agent(
    build_model(get_settings().LLM_MODEL_MINI),
    output_type=RouterDecision,
    system_prompt=PromptsOrganizer.ROUTER_SYSTEM,
)


async def route_decision(query: str) -> RouterDecision | None:
    """Classify route, reject not related queries."""
    try:
        result = await _route_agent.run(query, usage_limits=_ROUTER_LIMITS)
        return result.output
    except Exception:
        logger.exception("route_decision failed")
        return None
