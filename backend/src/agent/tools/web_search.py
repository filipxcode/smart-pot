import logging
from functools import lru_cache

from pydantic_ai import ModelRetry
from tavily import AsyncTavilyClient

from config.settings import get_settings

logger = logging.getLogger(__name__)

_UNAVAILABLE = (
    "Wyszukiwarka internetowa jest niedostępna (sprawdź konfigurację klucza API)."
)


@lru_cache
def _client(api_key: str) -> AsyncTavilyClient:
    return AsyncTavilyClient(api_key=api_key)


def _is_auth_error(exc: Exception) -> bool:
    """Twardy błąd konfiguracji (zły/odrzucony klucz) vs błąd przejściowy."""
    name = type(exc).__name__.lower()
    text = str(exc).lower()
    return (
        any(k in name for k in ("key", "auth", "unauthorized", "forbidden"))
        or any(k in text for k in ("api key", "401", "403", "unauthorized", "invalid key"))
    )


async def web_search(query: str) -> str:
    """Wyszukuje w internecie (Tavily) odpowiedzi na ogólne pytania —
    pielęgnacja roślin, botanika i inne ogólne tematy, których nie ma
    w dokumentach użytkownika."""
    api_key = get_settings().TAVILY_API_KEY
    if not api_key:
        logger.error("web_search: brak TAVILY_API_KEY")
        return _UNAVAILABLE

    logger.info("web_search: query=%r", query)
    try:
        data = await _client(api_key).search(
            query=query,
            search_depth="basic",
            max_results=5,
            include_answer=True,
        )
    except Exception as exc:
        if _is_auth_error(exc):
            logger.error("web_search: błąd uwierzytelniania Tavily: %s", exc)
            return _UNAVAILABLE
        logger.warning("web_search: błąd przejściowy: %s", exc)
        raise ModelRetry(
            "Wyszukiwanie w internecie chwilowo się nie powiodło. "
            "Spróbuj ponownie lub przeformułuj zapytanie."
        )

    answer = data.get("answer")
    results = data.get("results", [])
    if not answer and not results:
        raise ModelRetry("Brak wyników wyszukiwania. Spróbuj przeformułować zapytanie.")

    parts: list[str] = []
    if answer:
        parts.append(f"Podsumowanie z internetu: {answer}")
    for r in results:
        parts.append(
            f"[{r.get('title')}] {r.get('content')} (źródło: {r.get('url')})"
        )
    logger.info("web_search done: results=%d", len(results))
    return "\n\n".join(parts)
