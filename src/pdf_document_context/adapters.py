"""Normalize actual engine export formats; never treat detector output as proof."""
from .model import Block, Document


def role(value):
    value = str(value).lower().replace("_", " ")
    return {"section header": "heading", "title": "heading", "text": "paragraph",
            "list item": "list_item", "picture": "figure", "image": "figure",
            "page header": "header", "page footer": "footer"}.get(value, value)


def rectangle(box, height):
    if isinstance(box, (list, tuple)):
        # ODL JSON [left, bottom, right, top], bottom-left origin.
        left, bottom, right, top = map(float, box)
        return left, height - top, right, height - bottom
    left, top, right, bottom = (float(box[k]) for k in ("l", "t", "r", "b"))
    if str(box.get("coord_origin", "TOPLEFT")).upper() == "BOTTOMLEFT":
        top, bottom = height - top, height - bottom
    return left, top, right, bottom


def from_prepared(data: dict, version="unknown") -> Document:
    """Adapter for page/items preparation output, including OCR-backed analyses."""
    pages = {i: (float(p["width"]), float(p["height"]))
             for i, p in enumerate(data["pages"], 1)}
    blocks = []
    for page, p in enumerate(data["pages"], 1):
        for item in p["items"]:
            blocks.append(Block(f"docling:{item['id']}", page, tuple(item["rect"]),
                                role(item["role"]), item.get("text", ""), item["order"],
                                "docling", cells=item.get("cells", [])))
    return Document(pages, blocks, data.get("title", ""), {"docling": version}).validate()


def from_docling(data: dict, version="unknown") -> Document:
    """DoclingDocument.export_to_dict(), walking body refs in reading order."""
    pages = {int(k): (float(v["size"]["width"]), float(v["size"]["height"]))
             for k, v in data["pages"].items()}
    blocks = []
    visited = set()

    def walk(node):
        if "$ref" in node:
            ref = node["$ref"]
            if ref in visited:
                raise ValueError("Repeated or cyclic Docling reference")
            visited.add(ref)
            node = data
            for part in ref.removeprefix("#/").split("/"):
                node = node[int(part)] if isinstance(node, list) else node[part]
        label = node.get("label")
        for prov in node.get("prov", []) if label else []:
            page = int(prov["page_no"])
            text = node.get("text", "")
            cells = []
            for cell in node.get("data", {}).get("table_cells", []):
                cells.append({"text": cell.get("text", ""),
                              "row": int(cell["start_row_offset_idx"]) + 1,
                              "column": int(cell["start_col_offset_idx"]) + 1,
                              "header": bool(cell.get("column_header") or cell.get("row_header")),
                              "row_span": cell.get("row_span", 1),
                              "column_span": cell.get("col_span", 1)})
            blocks.append(Block(f"docling:{len(blocks)+1}", page,
                                rectangle(prov["bbox"], pages[page][1]), role(label), text,
                                len(blocks), "docling", node.get("level"), cells))
        for child in node.get("children", []):
            walk(child)

    walk(data["body"])
    if data.get("furniture"):
        walk(data["furniture"])
    title = next((b.text for b in blocks if b.role == "heading"), "")
    return Document(pages, blocks, title, {"docling": version}).validate()


def from_opendataloader(data: dict, pages: dict[int, tuple[float, float]],
                        version="unknown") -> Document:
    """ODL uses bottom-left coordinates; page sizes must come from the same PDF."""
    if int(data["number of pages"]) != len(pages):
        raise ValueError("Engine page counts differ")
    blocks = []

    def walk(node, inherited_page=None):
        kind = node.get("type", "")
        page = node.get("page number", inherited_page)
        page = int(page) if page is not None else None
        # Keep tables as single logical units with structured cells, not duplicate text.
        cells = []
        for row in node.get("rows", []):
            for c in row.get("cells", []):
                def texts(obj):
                    return [obj["content"]] if isinstance(obj.get("content"), str) else [
                        t for ch in obj.get("kids", []) for t in texts(ch)]
                cells.append({"text": " ".join(texts(c)), "row": c["row number"],
                              "column": c["column number"], "row_span": c.get("row span", 1),
                              "column_span": c.get("column span", 1)})
        content = node.get("content", "")
        if not isinstance(content, str):
            raise ValueError("ODL content must be text")
        if "bounding box" in node and (content or kind in {"table", "image", "picture"}):
            if page not in pages:
                raise ValueError("ODL item has no known page")
            identity = str(node.get("id", len(blocks)+1))
            blocks.append(Block("odl:"+identity, page,
                                rectangle(node["bounding box"], pages[page][1]), role(kind),
                                content, len(blocks), "opendataloader", node.get("heading level"),
                                cells, str(node["linked content id"]) if "linked content id" in node else None))
        if kind == "table":
            return
        for child in node.get("kids", []) + node.get("list items", []):
            walk(child, page)

    walk(data)
    return Document(pages, blocks, data.get("title") or "", {"opendataloader": version}).validate()
