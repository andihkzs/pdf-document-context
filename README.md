# PDF Document Context

**Version 0.1.2 — an experimental Python library for local PDF analysis and bounded LLM context.**

PDF Document Context reconciles **Docling** and **OpenDataLoader PDF** results, exposes disagreements and prepares context for translation or a later LLM assessment. The deterministic core has no third-party Python dependencies.

```text
PDF → Docling + OpenDataLoader → shared structure + unresolved differences
                                             ↓
                                bounded context / review plan
                                             ↓
                                  your translation application
```

The library does not modify PDFs, export PDF/UA or call LLM providers. The consuming application owns translation, layout rendering and human review.

## Features

| Feature | Behavior |
|---|---|
| Two local parsers | One sequential invocation per parser, without hybrid or cloud backends. |
| Shared document model | Pages, roles, heading levels, table cells, reading order and rectangles in PDF points from the top-left corner. |
| Evidence reconciliation | Matches using page, geometric overlap and text similarity. Flags differences in text, roles, tables and order. |
| Conservative decisions | Retains primary text and geometry; preserves ambiguous and unmatched content. Never automatically classifies content as decorative. |
| Bounded LLM context | Document title, role, same-page section path, nearby text, box dimensions, table cells and secondary evidence; at most 2,400 serialized JSON characters by default. |
| Review planning | At most two optional review requests per document by default. Additional unresolved items remain visible. No execution or retry loop. |
| Translation checks | Alerts for changed numbers, units, missing protected terms and empty translations. Does not establish semantic equivalence. |
| Input adapters | `DoclingDocument.export_to_dict()`, OpenDataLoader JSON and a simple `pages/items` preparation format. |
| Bounded Linux workers | Deadlines, cancellation callback, process-group termination, CPU/address-space/file limits and an inherited seccomp network filter. |

## Versions and prerequisites

The core supports **Python 3.11+**. Actual PDF extraction requires optional parser packages and preinstalled local models. Linux workers require **libseccomp** and fail closed if it is unavailable.

| Component | Reference version |
|---|---|
| PDF Document Context | **0.1.2**, schema **1.0** |
| Docling | **2.140.0** |
| OpenDataLoader PDF | **2.5.13** |
| Java | Upstream requires **11+**; tested with **OpenJDK 21** |
| Python | Core tests passed on **3.11–3.14** in GitHub Actions |
| PyMuPDF | **1.26.7**, used only to generate the optional integration-test fixture |

Other parser versions are not automatically compatible. `analyze` records installed parser versions. `merge` reports `unknown` for versionless external JSON. See [VERSIONS.md](VERSIONS.md) and [CHANGELOG.md](CHANGELOG.md).

## Installation

```bash
python -m venv .venv
. .venv/bin/activate
pip install .
pdf-document-context --version
```

For actual extraction:

```bash
pip install '.[engines]'
```

Install Java and libseccomp on Linux. Download Docling model files **before runtime**, following the [Docling documentation](https://docling-project.github.io/docling/usage/advanced_options/). Workers do not download missing models. Choose CPU/Torch packages compatible with your platform. Parsers may run in separate Python environments.

## Try the core without parsers or an LLM

```bash
python examples/synthetic_demo.py
python -B -m unittest discover -s tests -v
```

The fabricated example has one parser read `12 V` and the other `24 V`. The primary wording is retained and the disagreement is flagged. Only this synthetic example prints context to stdout.

## Run both parsers

```bash
pdf-document-context analyze input.pdf \
  --docling-artifacts /path/to/preinstalled/docling-models \
  --java-home /path/to/jdk \
  --output report.json
```

For separate environments, add `--docling-python /path/to/docling/bin/python` and `--odl-python /path/to/odl/bin/python`. The default deadline is 120 seconds **per engine**, run sequentially. [examples/real_engines.py](examples/real_engines.py) provides an opt-in two-page fixture with a heading, paragraphs and a ruled table. It makes no cloud calls.

To merge existing exports:

```bash
pdf-document-context merge docling.json opendataloader.json --output report.json
```

Both exports must describe the same PDF. Matching dimensions alone do not establish source identity; callers of `merge` must ensure this. `analyze` supplies identical bytes to both parsers.

## Python API

```python
from pdf_document_context import (
    from_docling, from_opendataloader, reconcile,
    context_for, review_requests, check_translation,
)

primary = from_docling(docling_export, version="2.140.0")
secondary = from_opendataloader(odl_export, primary.pages, version="2.5.13")
document = reconcile(primary, secondary)

context = context_for(document, document.blocks[0].id)
plan = review_requests(document)  # Data only; no provider calls.
check = check_translation("Use 12 V Basic", "Utiliser 12 V Basic", ["Basic"])
```

A translation application can send `context` alongside the text to its selected model. Document contents remain **untrusted input data**, never system instructions. Additional context consumes input tokens. Better translation quality or lower overall cost requires measurement rather than assumption.

Only detected disagreements produce review plans. The application separately owns consent, cost accounting, model choice and request timeouts. This library contains no provider keys, automatic inference or unbounded correction loops.

## Privacy and operating limits

- No provider clients, credential forwarding or cloud calls. Offline flags and seccomp rules deny `connect`, `sendto`, `sendmsg` and `sendmmsg`, including in child Java processes. This is not a complete sandbox for malicious code.
- Workers receive a small explicit environment. Temporary PDFs/JSON default to Linux `/dev/shm` and are removed after success, error or cancellation. Another `--temporary-root` may use persistent storage. RAM filesystems also depend on host swap settings.
- Explicit JSON reports **contain document text** and remain at the requested output path. The CLI creates reports with mode `0600` and refuses to overwrite an existing file. Normal CLI logs do not include document text or parser output.
- Default limits: 15 MiB PDF, 20 pages, 1,500 normalized blocks, 45,000 extracted characters and 600 cells per table. Workers: 6 GiB virtual address space, 110/115 CPU seconds, 32 MiB per written file, 256 open files and a 512 MiB JVM heap. Services should add host/container memory limits.
- `runner.extract` checks `cancel` while a worker runs. Each parser gets one attempt. Errors do not trigger another provider.
- Image extraction is disabled in the local OpenDataLoader worker; header/footer text is retained.
- `runner.extract(..., include_hidden_text=True)` explicitly includes invisible text layers in OpenDataLoader analysis. Use this for a locally prepared OCR copy; the default keeps the upstream hidden-text filter enabled. This does not make document content trusted or safe as instructions.
- The runner does not perform OCR. Prepare scans locally first. An existing OCR/Docling preparation can be supplied through `from_prepared` and compared against OpenDataLoader results for the same prepared PDF without running Docling again.

## Assessment limits

Both parsers can agree and still be wrong. Overlap and similarity scores are **not calibrated probabilities**. Split/merge cases, complex tables, cross-page section hierarchies, complex scripts and rotated pages are not comprehensively resolved. Table cells are contextual data and are not automatically attached to every separate translation block by this library.

Review planning is an initial shortlist. The library neither generates image descriptions nor judges warning semantics. Numeric checks conservatively flag changed decimal notation and do not replace a subject-matter translation review.

The source PDF is not rewritten. This library alone produces neither a translated PDF nor an accessible PDF. The exporting application must provide PDF/UA validation, human review and an actual layout comparison. [veraPDF performs only machine-verifiable PDF/UA checks](https://docs.verapdf.org/validation/).

## License and upstream projects

Original library code: [MIT](LICENSE). Docling and OpenDataLoader are separate projects with their own licenses. Their packages and models are not bundled in this repository.

- [Docling](https://github.com/docling-project/docling)
- [OpenDataLoader PDF](https://github.com/opendataloader-project/opendataloader-pdf)
- [OpenDataLoader JSON schema](https://opendataloader.org/docs/reference/json-schema)
