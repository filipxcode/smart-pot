import logging

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage
from pydantic_ai.usage import UsageLimits

from agent.deps import ChatDeps
from agent.model import build_model
from agent.prompts.prompts import PromptsOrganizer
from agent.tools.read_historical_data import read_historical_data
from agent.tools.read_sensor import read_sensor
from agent.tools.schedule_watering import schedule_watering_plant
from agent.tools.search_document import search_document
from agent.tools.water_plant import water_plant
from agent.tools.web_search import web_search
from config.settings import get_settings

logger = logging.getLogger(__name__)

_tool_agent = Agent(
    build_model(get_settings().LLM_MODEL),
    deps_type=ChatDeps,
    output_type=str,
    system_prompt=PromptsOrganizer.TOOL_SYSTEM,
    tools=[
        read_sensor,
        read_historical_data,
        schedule_watering_plant,
        search_document,
        water_plant,
        web_search,
    ],
)

_TOOL_LIMITS = UsageLimits(request_limit=12, tool_calls_limit=10)


async def tool_answer(
    query: str,
    deps: ChatDeps,
    history: list[ModelMessage] | None = None,
) -> str:
    logger.info("tool_answer: query=%r", query)
    try:
        result = await _tool_agent.run(
            query, deps=deps, message_history=history or [], usage_limits=_TOOL_LIMITS
        )
        answer = result.output
        logger.info("tool_answer done: answer_chars=%d", len(answer))
        return answer
    except Exception:
        logger.exception("tool_answer failed")
        return PromptsOrganizer.ERROR_MESSAGE