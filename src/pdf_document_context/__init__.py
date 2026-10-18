"""Deterministic local structure reconciliation; no model-provider client."""
from .adapters import from_docling, from_opendataloader, from_prepared
from .analysis import reconcile, context_for, review_requests, check_translation
from .model import Block, Document, Limits

__version__ = "0.1.0"
__all__ = ["Block", "Document", "Limits", "from_docling", "from_opendataloader",
           "from_prepared", "reconcile", "context_for", "review_requests", "check_translation"]
