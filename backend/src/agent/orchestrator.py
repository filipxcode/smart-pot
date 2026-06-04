import logging

import logfire
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
from agent.retrieval.rag_search import ChunkHit
from agent.router import route_decision
from agent.tool_agent import tool_answer

logger = logging.getLogger(__name__)


async def run_turn(
    query: str,
    deps: ChatDeps,
    history: list[ModelMessage] | None = None,
) -> tuple[str, list[ChunkHit], list[ModelMessage]]:
    with logfire.span("run_turn", query=query) as span:
        compacted = await compact_history(history or [])
        decision = await route_decision(query)
        decision_label = decision.decision if decision else "error"
        span.set_attribute("decision", decision_label)
        logger.info("run_turn: decision=%s", decision_label)

        answer: str
        sources: list[ChunkHit] = []

        match decision_label:
            case "tool":
                answer = await tool_answer(query=query, deps=deps, history=compacted)
            case "reject":
                answer = PromptsOrganizer.REJECT_MESSAGE
            case _: 
                answer = PromptsOrganizer.ERROR_MESSAGE

        new_history = compacted + [
            ModelRequest(parts=[UserPromptPart(content=query)]),
            ModelResponse(parts=[TextPart(content=answer)]),
        ]
        return answer, sources, new_history
