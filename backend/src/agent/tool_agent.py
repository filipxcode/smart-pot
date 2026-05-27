import logging

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage

from agent.deps import ChatDeps
from agent.prompts.prompts import PromptsOrganizer
from config.settings import get_settings

logger = logging.getLogger(__name__)

_tool_agent = Agent(
    get_settings().LLM_MODEL,
    output_type=str,
    system_prompt=PromptsOrganizer.TOOL_SYSTEM,
)


async def tool_answer(
    query: str,
    deps: ChatDeps,
    history: list[ModelMessage] | None = None,
) -> str:
    logger.info("tool_answer: query=%r", query)
    result = await _tool_agent.run(query, deps=deps, message_history=history or [])
    answer = result.output
    logger.info("tool_answer done: answer_chars=%d", len(answer))
    return answer