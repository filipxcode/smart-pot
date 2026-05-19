from openai import AsyncOpenAI
import logging 

logger = logging.getLogger(__name__)

async def embed_batch(client: AsyncOpenAI, model: str, texts: list[str]) -> list[list[float]]:
    logger.info("Started embeddings batch")
    if not texts:
        return []
    try:
        response = await client.embeddings.create(model=model, input=texts)
    except Exception as e:
        logger.error(f"Error in batch embbeding: {e}")
        raise 
    return [item.embedding for item in response.data]

async def embed_one(client: AsyncOpenAI, model: str, texts: list[str]) -> list[float]:
    logger.info("Started embeddings single")
    if not texts:
        return []
    try:
        response = await client.embeddings.create(model=model, input=texts)
    except Exception as e:
        logger.error(f"Error in single embbeding: {e}")
        raise 
    return response.data[0].embedding