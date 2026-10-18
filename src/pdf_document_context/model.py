"""The canonical coordinate space is points from the top left, per page."""
from dataclasses import asdict, dataclass, field
import math


@dataclass(frozen=True)
class Limits:
    max_pages: int = 20
    max_blocks: int = 1500
    max_characters: int = 45000
    max_input_bytes: int = 15 * 1024**2
    max_json_bytes: int = 32 * 1024**2
    context_characters: int = 2400
    max_review_requests: int = 2


@dataclass
class Block:
    id: str
    page: int
    rect: tuple[float, float, float, float]
    role: str
    text: str
    order: int
    engine: str
    level: int | None = None
    cells: list[dict] = field(default_factory=list)
    caption_of: str | None = None
    evidence: list[dict] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)


@dataclass
class Document:
    pages: dict[int, tuple[float, float]]
    blocks: list[Block]
    title: str = ""
    engines: dict[str, str] = field(default_factory=dict)
    schema_version: str = "1.0"

    def validate(self, limits: Limits = Limits()):
        if not 1 <= len(self.pages) <= limits.max_pages:
            raise ValueError("Page limit exceeded or no pages")
        for number, size in self.pages.items():
            if number < 1 or len(size) != 2 or not all(math.isfinite(v) and v > 0 for v in size):
                raise ValueError("Invalid page dimensions")
        if len(self.blocks) > limits.max_blocks:
            raise ValueError("Block limit exceeded")
        ids = set()
        count = 0
        for b in self.blocks:
            if not b.id or len(b.id)>128 or len(b.role)>64 or b.id in ids or b.page not in self.pages:
                raise ValueError("Duplicate block ID or unknown page")
            ids.add(b.id)
            if len(b.rect) != 4 or not all(math.isfinite(v) for v in b.rect):
                raise ValueError("Invalid block coordinates")
            x0, y0, x1, y1 = b.rect
            w, h = self.pages[b.page]
            if not (0 <= x0 < x1 <= w + .1 and 0 <= y0 < y1 <= h + .1):
                raise ValueError("Block outside page")
            count += len(b.text) + sum(len(c.get("text", "")) for c in b.cells)
            if len(b.cells)>600:
                raise ValueError("Table cell limit exceeded")
        if count > limits.max_characters:
            raise ValueError("Extracted character limit exceeded")
        return self

    def to_dict(self):
        return asdict(self)
