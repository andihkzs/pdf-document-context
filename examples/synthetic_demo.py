"""No optional engines needed. Fabricated content only; prints local context."""
import json
from pdf_document_context import from_prepared, from_opendataloader, reconcile, context_for, review_requests, check_translation

prepared = {"title": "Solar Repeller Basic", "pages": [{"width": 600, "height": 800, "items": [
    {"id": "title", "role": "title", "text": "Solar Repeller Basic", "rect": [40,40,400,65], "order": 0},
    {"id": "warning", "role": "text", "text": "Use only 12 V power.", "rect": [40,100,400,125], "order": 1},
]}]}
odl = {"number of pages": 1, "kids": [
    {"id": 1, "type": "heading", "heading level": 1, "content": "Solar Repeller Basic", "page number": 1, "bounding box": [40,735,400,760]},
    {"id": 2, "type": "paragraph", "content": "Use only 24 V power.", "page number": 1, "bounding box": [40,675,400,700]},
]}
first = from_prepared(prepared, "synthetic")
combined = reconcile(first, from_opendataloader(odl, first.pages, "synthetic"))
print(json.dumps({"context": context_for(combined,"docling:warning"),
                  "review_plan": review_requests(combined),
                  "translation_check": check_translation("Use 12 V Basic", "Utiliser 24 W Base", ["Basic"])}, indent=2))
