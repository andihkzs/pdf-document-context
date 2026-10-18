# Versions and compatibility

## 0.1.1

English documentation, examples and release descriptions. No model-provider integration is included in the library. The Python API and schema remain compatible with 0.1.0.

| Interface | Version / evidence |
|---|---|
| Library | `pdf-document-context==0.1.1` |
| Shared JSON schema | `1.0`, `Document.schema_version` |
| Primary adapter | Docling `2.140.0`, `DoclingDocument.export_to_dict()` |
| Secondary adapter | OpenDataLoader PDF `2.5.13`, `format="json"` |
| Prepared-input adapter | `pages` with `width`, `height`, `items`; each item has `id`, `role`, `text`, `rect`, `order`, optional `cells` |
| Real integration test | Controller and OpenDataLoader on Python 3.14, Docling on Python 3.12, OpenJDK 21, CPU, preinstalled Docling models |
| PDF fixture generation | PyMuPDF `1.26.7`; not a runtime dependency |

The optional `engines` dependency group pins both parser versions. Transitive dependencies and model files are not fully locked. Production deployments should also maintain platform-specific lockfiles and model checksums. Passing the example does not establish quality on arbitrary PDFs.

Verification for 0.1.0: 19 tests passed locally on Python 3.12 and 3.14 and in GitHub Actions on Python 3.11–3.14. The real two-page fixture produced five primary blocks, four secondary blocks, six combined blocks and three explicit differences. Both engines detected the table; all contexts remained within budget; no LLM calls occurred. Segmentation differences intentionally remain unresolved. These tests do not establish PDF/UA conformance or translation quality.

When upgrading a parser, run the real text/table fixture, check coordinate conversion, compare outputs and update this matrix. Do not silently adapt an unverified schema.
