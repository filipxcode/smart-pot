from typing import Literal

from pydantic import BaseModel
from pydantic_ai import Agent

from agent.model import build_model
from agent.prompts.prompts import PromptsOrganizer
from config.settings import get_settings


class RouterDecision(BaseModel):
    decision: Literal["tool", "reject", "rag"]


_route_agent = Agent(
    build_model(get_settings().LLM_MODEL_MINI),
    output_type=RouterDecision,
    system_prompt=PromptsOrganizer.ROUTER_SYSTEM,
)


async def route_decision(query: str) -> RouterDecision:
    result = await _route_agent.run(query)
    return result.output
