import argparse
import json
import os
from pathlib import Path
import sys
from . import __version__, from_docling, from_opendataloader, reconcile, review_requests
from .model import Limits
from .runner import extract, EngineError


def main():
    parser = argparse.ArgumentParser(description="Local PDF structure evidence and bounded LLM review plans")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    merge = sub.add_parser("merge", help="Combine existing Docling and OpenDataLoader JSON")
    merge.add_argument("docling", type=Path)
    merge.add_argument("opendataloader", type=Path)
    analyze = sub.add_parser("analyze", help="Run both local engines on the same PDF (Linux)")
    analyze.add_argument("pdf", type=Path)
    analyze.add_argument("--docling-artifacts", type=Path, required=True)
    analyze.add_argument("--docling-python", default=sys.executable)
    analyze.add_argument("--odl-python", default=sys.executable)
    analyze.add_argument("--java-home", type=Path)
    analyze.add_argument("--temporary-root", default="/dev/shm", type=Path)
    analyze.add_argument("--timeout", type=float, default=120, help="Seconds per engine, no retry")
    for cmd in [merge, analyze]:
        cmd.add_argument("--output", type=Path, required=True)
        cmd.add_argument("--max-review-requests", type=int, default=2)
    args = parser.parse_args()
    if not 0 <= args.max_review_requests <= 10:
        parser.error("--max-review-requests must be between 0 and 10")
    if args.output.exists():
        parser.error("Output already exists; choose a new report path")
    limits = Limits(max_review_requests=args.max_review_requests)
    try:
        if args.command == "merge":
            def load(path):
                if path.stat().st_size > limits.max_json_bytes:raise ValueError("JSON too large")
                return json.loads(path.read_text())
            a, b = load(args.docling), load(args.opendataloader)
            first = from_docling(a)
            second = from_opendataloader(b, first.pages)
        else:
            if args.pdf.stat().st_size > limits.max_input_bytes:raise ValueError("PDF too large")
            pdf = args.pdf.read_bytes()
            a = extract(pdf, "docling", python=args.docling_python, artifacts=args.docling_artifacts,
                        temporary_root=args.temporary_root, timeout=args.timeout)
            first = from_docling(a["data"], a["version"])
            b = extract(pdf, "opendataloader", python=args.odl_python, java_home=args.java_home,
                        temporary_root=args.temporary_root, timeout=args.timeout)
            second = from_opendataloader(b["data"], first.pages, b["version"])
        doc = reconcile(first, second, limits)
        report = {"library_version": __version__, "document": doc.to_dict(),
                  "review_plan": review_requests(doc, limits),
                  "pdfua_validated": False, "llm_calls": 0}
        # Reports contain document content. Explicit output only, never stdout/logs.
        encoded = json.dumps(report, ensure_ascii=False, indent=2)
        fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as output:
            output.write(encoded)
    except (EngineError, ValueError, KeyError, OSError, StopIteration, RecursionError, TypeError):
        parser.exit(2, "Analysis failed: check input schema, engine installation, limits and offline models.\n")
    print("Local analysis complete. Report written; no LLM calls or PDF modifications.")
