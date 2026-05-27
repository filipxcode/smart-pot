from pydantic_ai import RunContext, ModelRetry
from agent.tool_agent import _tool_agent
from datetime import datetime

@_tool_agent.tool
async def schedule_watering_plant(date: datetime, ctx: RunContext)->str:
    #here schedule
    return "Success"