from pydantic_ai import RunContext, ModelRetry
from agent.tool_agent import _tool_agent

@_tool_agent.tool
async def read_sensor(name: str, ctx: RunContext)->str:
    #here water func
    return "25 stopni"