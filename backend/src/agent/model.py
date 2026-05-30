from functools import lru_cache

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from config.settings import get_settings


@lru_cache
def build_model(name: str) -> OpenAIChatModel:
    return OpenAIChatModel(
        name,
        provider=OpenAIProvider(api_key=get_settings().OPENAI_API_KEY),
    )
