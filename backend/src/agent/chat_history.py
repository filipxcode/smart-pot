from pydantic_ai import Agent
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    SystemPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)

from agent.prompts.prompts import PromptsOrganizer
from config.settings import get_settings

MAX_MESSAGES_BEFORE_COMPACT = 20
KEEP_RECENT = 6

_summary_agent = Agent(
    get_settings().LLM_MODEL_MINI,
    output_type=str,
    system_prompt=PromptsOrganizer.HISTORY_SUMMARY_SYSTEM,
)


async def compact_history(
    messages: list[ModelMessage],
    max_messages: int = MAX_MESSAGES_BEFORE_COMPACT,
) -> list[ModelMessage]:
    """Jeśli historia <= max_messages, zwróć bez zmian.
    Inaczej streszcz środek, zachowując system prompt (jeśli jest)
    i ostatnie KEEP_RECENT wiadomości w oryginale."""
    if len(messages) < max_messages:
        return messages

    system_msg = messages[0] if messages and _has_system(messages[0]) else None
    middle_start = 1 if system_msg else 0
    middle = messages[middle_start:-KEEP_RECENT]
    recent = messages[-KEEP_RECENT:]

    if not middle:
        return messages

    summary_text = await _summarize_messages(middle)
    summary_msg = _make_summary_message(summary_text)

    new_history: list[ModelMessage] = []
    if system_msg:
        new_history.append(system_msg)
    new_history.append(summary_msg)
    new_history.extend(recent)
    return new_history


async def _summarize_messages(messages: list[ModelMessage]) -> str:
    text = _format_messages_for_summary(messages)
    result = await _summary_agent.run(text)
    return result.output


def _format_messages_for_summary(messages: list[ModelMessage]) -> str:
    """Return flat message history"""
    lines: list[str] = []
    for msg in messages:
        if isinstance(msg, ModelRequest):
            for part in msg.parts:
                if isinstance(part, UserPromptPart):
                    lines.append(f"User: {part.content}")
                elif isinstance(part, ToolReturnPart):
                    lines.append(f"Tool[{part.tool_name}] -> {part.content}")
        elif isinstance(msg, ModelResponse):
            for part in msg.parts:
                if isinstance(part, TextPart):
                    lines.append(f"Assistant: {part.content}")
                elif isinstance(part, ToolCallPart):
                    lines.append(
                        f"Assistant -> tool_call {part.tool_name}({part.args})"
                    )
    return "\n".join(lines)


def _make_summary_message(summary_text: str) -> ModelMessage:
    return ModelRequest(parts=[
        UserPromptPart(
            content=f"[Streszczenie wcześniejszej rozmowy]\n{summary_text}"
        )
    ])


def _has_system(msg: ModelMessage) -> bool:
    return isinstance(msg, ModelRequest) and any(
        isinstance(p, SystemPromptPart) for p in msg.parts
    )
