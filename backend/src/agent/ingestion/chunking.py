import logging

from langchain_core.documents import Document
from langchain_text_splitters import (
    Language,
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from config.settings import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

_HEADERS_TO_SPLIT_ON = [
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3"),
    ("####", "h4"),
]

_markdown_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=_HEADERS_TO_SPLIT_ON,
)

_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    encoding_name=settings.EMBEDDING_ENCODING,
    chunk_size=settings.CHUNK_SIZE,
    chunk_overlap=settings.CHUNK_OVERLAP,
    separators=RecursiveCharacterTextSplitter.get_separators_for_language(
        Language.MARKDOWN,
    ),
)


def chunk_text(text: str) -> list[Document]:
    """Chunk function based on markdown splitting, if header length is too big then recursively splitting to smaller chunks"""
    if not text:
        return []

    sections = _markdown_splitter.split_text(text)
    chunks = _splitter.split_documents(sections)

    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i

    logger.info(
        "Chunked text of %d chars into %d chunks across %d sections",
        len(text),
        len(chunks),
        len(sections),
    )
    return chunks
