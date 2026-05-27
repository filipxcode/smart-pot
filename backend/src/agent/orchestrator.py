import logging

from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)

from agent.chat_history import compact_history
from agent.deps import ChatDeps
from agent.prompts.prompts import PromptsOrganizer
from agent.rag_agent import rag_answer
from agent.retrieval.rag_search import ChunkHit
from agent.router import route_decision
from agent.tool_agent import tool_answer

logger = logging.getLogger(__name__)


async def run_turn(
    query: str,
    deps: ChatDeps,
    history: list[ModelMessage] | None = None,
) -> tuple[str, list[ChunkHit], list[ModelMessage]]:
    compacted = await compact_history(history or [])
    decision = await route_decision(query)
    logger.info("run_turn: decision=%s", decision.decision)

    answer: str
    sources: list[ChunkHit] = []

    match decision.decision:
        case "rag":
            answer, sources = await rag_answer(query=query, deps=deps, history=compacted)
        case "tool":
            answer = await tool_answer(query=query, deps=deps, history=compacted)
        case "reject":
            answer = PromptsOrganizer.REJECT_MESSAGE

    new_history = compacted + [
        ModelRequest(parts=[UserPromptPart(content=query)]),
        ModelResponse(parts=[TextPart(content=answer)]),
    ]
    return answer, sources, new_history
