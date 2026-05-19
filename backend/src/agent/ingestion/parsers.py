import logging
from collections import Counter
from pathlib import Path

import fitz

logger = logging.getLogger(__name__)

_MAX_HEADING_LEVEL = 4
_MIN_HEADING_RATIO = 1.05
_BOLD_FLAG = 1 << 4


def parse_pdf(source: str | Path | bytes) -> str:
    """Parse a PDF into markdown with `#`..`####` headers compatible with the chunker.

    Heading levels are inferred from font sizes: the body size is the most
    common rounded size, and the largest sizes above it map to `#` through
    `####`. Bold lines slightly above body size are promoted to `####`.
    """
    if isinstance(source, (str, Path)):
        doc = fitz.open(source)
    else:
        doc = fitz.open(stream=source, filetype="pdf")

    try:
        lines = _collect_lines(doc)
    finally:
        doc.close()

    if not lines:
        return ""

    size_to_level = _build_heading_map([line["size"] for line in lines])
    return _render_markdown(lines, size_to_level)


def _collect_lines(doc: "fitz.Document") -> list[dict]:
    lines: list[dict] = []
    for page in doc:
        blocks = page.get_text("dict").get("blocks", [])
        for block in blocks:
            if block.get("type", 0) != 0:
                continue
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                text = "".join(span.get("text", "") for span in spans).strip()
                if not text:
                    continue
                sizes = [span.get("size", 0.0) for span in spans if span.get("text", "").strip()]
                if not sizes:
                    continue
                max_size = max(sizes)
                is_bold = any(
                    (span.get("flags", 0) & _BOLD_FLAG)
                    or "bold" in span.get("font", "").lower()
                    for span in spans
                    if span.get("text", "").strip()
                )
                lines.append(
                    {
                        "text": text,
                        "size": round(max_size, 1),
                        "bold": is_bold,
                    }
                )
    return lines


def _build_heading_map(sizes: list[float]) -> dict[float, int]:
    counts = Counter(sizes)
    body_size = counts.most_common(1)[0][0]
    heading_sizes = sorted(
        {s for s in sizes if s >= body_size * _MIN_HEADING_RATIO},
        reverse=True,
    )[:_MAX_HEADING_LEVEL]
    return {size: level + 1 for level, size in enumerate(heading_sizes)}


def _render_markdown(lines: list[dict], size_to_level: dict[float, int]) -> str:
    body_level = _MAX_HEADING_LEVEL
    parts: list[str] = []
    prev_was_heading = False

    for line in lines:
        level = size_to_level.get(line["size"])
        if level is None and line["bold"] and not size_to_level:
            level = body_level
        if level is not None:
            if parts and not prev_was_heading:
                parts.append("")
            parts.append(f"{'#' * level} {line['text']}")
            prev_was_heading = True
        else:
            parts.append(line["text"])
            prev_was_heading = False

    markdown = "\n".join(parts).strip()
    logger.info("Parsed PDF into %d lines (%d heading sizes)", len(lines), len(size_to_level))
    return markdown
