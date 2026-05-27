from pydantic_ai import RunContext, ModelRetry
from agent.tool_agent import _tool_agent

@_tool_agent.tool
async def water_plant(watering_time: int, ctx: RunContext)->str:
    #here water func
    return "Success"