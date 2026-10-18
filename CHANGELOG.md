# Changelog

## 0.1.2 — 2026-10-18

- Disable unnecessary image-file extraction in the OpenDataLoader worker.
- Retain header/footer text and add explicit `include_hidden_text` opt-in for locally prepared OCR layers.
- Keep upstream hidden-text filtering enabled by default.

## 0.1.1 — 2026-10-18

- Translate repository documentation, example comments and public release descriptions into English.
- Document reuse of existing OCR/Docling preparation without a second primary-parser run.
- Keep the Python API and schema compatible with 0.1.0.

## 0.1.0 — 2026-10-18

- Shared local document structure for Docling and OpenDataLoader.
- Adapters for actual JSON exports and prepared OCR/structure data.
- Conservative evidence reconciliation with explicit disagreements.
- Bounded LLM context and at most two planned optional reviews by default.
- Local alerts for changed numbers, units and protected terms.
- CLI for PDF analysis and merging existing exports.
- Bounded Linux workers with cancellation and inherited network filtering.
- Synthetic examples, tests and CI for the independent core.
- Initial release does not modify PDFs or implement PDF/UA validation.
