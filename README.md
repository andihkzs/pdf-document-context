# PDF Document Context

**Version 0.1.0 — experimentelle Python-Bibliothek für lokale PDF-Analyse und besseren LLM-Kontext.**

PDF Document Context führt Ergebnisse von **Docling** und **OpenDataLoader PDF** zusammen. Es macht Unterschiede sichtbar und erstellt begrenzte Kontextdaten für eine Übersetzung oder eine spätere LLM-Beurteilung. Der eigene Kern benötigt keine externen Python-Pakete.

```text
PDF → Docling + OpenDataLoader → gemeinsame Struktur + offene Unterschiede
                                      ↓
                          begrenzter Kontext / Prüfplan
                                      ↓
                         eigene Übersetzungsanwendung
```

Die Bibliothek verändert kein PDF, exportiert kein PDF/UA und führt keine LLM-Anfragen aus. Sie liefert Hilfsdaten für eine Anwendung, die Übersetzung, Layout und menschliche Prüfung separat verantwortet.

## Funktionen in 0.1.0

| Funktion | Verhalten |
|---|---|
| Zwei lokale Parser | Einmalige, nacheinander ausgeführte Analyse mit Docling und OpenDataLoader; kein Hybrid-/Cloud-Backend. |
| Gemeinsames Datenmodell | Seiten, Textrollen, Überschriftenebenen, Tabellenzellen, Reihenfolge und Rechtecke. Koordinaten einheitlich in PDF-Punkten ab der linken oberen Ecke. |
| Quellenvergleich | Zuordnung anhand Seite, geometrischer Überdeckung und Textähnlichkeit. Unterschiedliche Texte, Rollen, Tabellen und Reihenfolgen werden markiert. |
| Konservative Entscheidungen | Primärtext und Geometrie bleiben erhalten. Mehrdeutige Zuordnungen und zusätzliche Elemente werden nicht stillschweigend verworfen. Keine automatische Einstufung als Dekoration. |
| LLM-Kontext | Dokumenttitel, Textrolle, Abschnitt auf derselben Seite, Nachbartext, Feldabmessungen, Tabellenzellen und Gegenbefunde. Standardmäßig höchstens 2.400 serialisierte JSON-Zeichen pro Kontext. |
| Prüfplan | Standardmäßig maximal zwei optionale Prüfaufträge pro Dokument; weitere offene Stellen bleiben ausgewiesen. Keine Ausführung und keine Wiederholungslogik. |
| Übersetzungskontrolle | Hinweise bei geänderten Zahlen, Einheiten, fehlenden geschützten Begriffen oder leerer Übersetzung. Keine Bestätigung semantischer Gleichheit. |
| Eingangsadapter | `DoclingDocument.export_to_dict()`, OpenDataLoader-JSON und ein einfaches `pages/items`-Vorbereitungsformat. |
| Begrenzte Worker | Zeitlimit, Abbruch-Callback, Prozessgruppen-Abbruch, CPU-/Adressraum-/Dateigrößenlimits und ein vererbter Linux-seccomp-Netzwerkfilter. |

## Versionen und Voraussetzungen

Die Kernbibliothek unterstützt Python **3.11+**. Die echten Parser benötigen zusätzliche Pakete und lokale Modelle. Die Linux-Worker verlangen **libseccomp**, sonst brechen sie ab.

| Komponente | Referenz für 0.1.0 |
|---|---|
| PDF Document Context | **0.1.0**, Datenformat **1.0** |
| Docling | **2.140.0** |
| OpenDataLoader PDF | **2.5.13** |
| Java für OpenDataLoader | Upstream-Voraussetzung **11+**; Integration mit **OpenJDK 21** geprüft |
| Python | Lokale Kerntests mit **3.12 und 3.14**; CI-Matrix für **3.11–3.14** |
| PyMuPDF | **1.26.7**, ausschließlich für das optionale synthetische Integrationstest-Beispiel |

Andere Parser-Versionen sind nicht pauschal kompatibel. `analyze` schreibt die tatsächlich installierten Parser-Versionen in den Bericht. `merge` markiert Versionen als `unknown`, wenn reine Fremd-JSON-Dateien ohne Versionsnachweis übergeben werden. Details und Änderungsverlauf: [VERSIONS.md](VERSIONS.md), [CHANGELOG.md](CHANGELOG.md).

## Installation

```bash
python -m venv .venv
. .venv/bin/activate
pip install .
pdf-document-context --version
```

Für die tatsächliche PDF-Analyse zusätzlich:

```bash
pip install '.[engines]'
```

Java und libseccomp müssen auf Linux vorhanden sein. Docling-Modelle **vorab** gemäß [Docling-Dokumentation](https://docling-project.github.io/docling/usage/advanced_options/) herunterladen; der Worker lädt zur Laufzeit keine Modelle nach. CPU-/Torch-Installation muss zur jeweiligen Plattform passen. Die Parser können auch in getrennten Python-Umgebungen installiert werden.

## Schnell ausprobieren, ohne Parser oder LLM

```bash
python examples/synthetic_demo.py
python -B -m unittest discover -s tests -v
```

Das Beispiel verwendet frei erfundene Daten: Ein Parser liest `12 V`, der andere `24 V`. Der eigene Code erhält die Primärfassung und markiert den Unterschied. Nur dieses synthetische Beispiel schreibt Kontext auf stdout.

## Beide Parser auf einem PDF ausführen

```bash
pdf-document-context analyze input.pdf \
  --docling-artifacts /path/to/preinstalled/docling-models \
  --java-home /path/to/jdk \
  --output report.json
```

Bei getrennten Umgebungen `--docling-python /path/to/docling/bin/python` und `--odl-python /path/to/odl/bin/python` ergänzen. Standard-Zeitlimit: 120 Sekunden **je Parser**, nacheinander. Für den echten synthetischen Zwei-Seiten-Test siehe [examples/real_engines.py](examples/real_engines.py); er enthält Überschrift, Absatz und eine gezeichnete Tabelle und erzeugt keine Cloud-Anfragen.

Vorhandene Exporte kombinieren:

```bash
pdf-document-context merge docling.json opendataloader.json --output report.json
```

Beide Exporte müssen dasselbe PDF beschreiben. Übereinstimmende Maße allein beweisen nicht, dass die Quelldateien identisch sind; bei `merge` trägt der Aufrufer die Verantwortung. `analyze` übergibt exakt dieselben Bytes an beide Parser.

## Python-Schnittstelle

```python
from pdf_document_context import (
    from_docling, from_opendataloader, reconcile,
    context_for, review_requests, check_translation,
)

primary = from_docling(docling_export, version="2.140.0")
secondary = from_opendataloader(odl_export, primary.pages, version="2.5.13")
document = reconcile(primary, secondary)

context = context_for(document, document.blocks[0].id)
plan = review_requests(document)  # Daten, keine API-Anfragen
check = check_translation("Use 12 V Basic", "Utiliser 12 V Basic", ["Basic"])
```

Eine Übersetzungsanwendung kann `context` zusammen mit dem zu übersetzenden Text an ihr gewähltes Modell senden. Dokumentinhalt bleibt dabei **unvertrauenswürdige Eingabedaten**, keine Systemanweisung. Zusätzlicher Kontext verbraucht beim Modell Eingabe-Tokens. Ein kleinerer Gesamtpreis oder bessere Übersetzungsqualität ist ohne Vergleichstest nicht nachgewiesen.

Prüfaufträge werden nur für erkannte Unstimmigkeiten geplant. Eine Anwendung entscheidet separat über Freigabe, Kostenprotokoll, Zeitlimit und Modell. Die Bibliothek enthält bewusst keinen Provider-Schlüssel, keine automatische Ausführung und keine unbeschränkten Korrekturschleifen.

## Datenschutz und Betriebsgrenzen

- Keine Provider-Clients, keine Schlüsselweitergabe an Worker, keine Cloud-Anfragen durch diese Bibliothek. Offline-Modellflags und ein seccomp-Filter gegen `connect`, `sendto`, `sendmsg` und `sendmmsg` gelten auch für gestartetes Java. Das ist keine vollständige Sandbox gegen schädlichen Code.
- Parser laufen mit einer kleinen expliziten Umgebung. Standard-Temporärverzeichnis ist `/dev/shm` auf Linux; dort werden PDF/JSON kurzzeitig angelegt und beim Ende oder Abbruch entfernt. Ein anderes `--temporary-root` kann auf persistentem Speicher liegen. Auch RAM-Dateisysteme hängen von Swap- und Host-Einstellungen ab.
- Der ausdrücklich gewählte JSON-Bericht **enthält Dokumenttext** und bleibt auf dem Rechner des Aufrufers gespeichert. Die CLI legt ihn mit Dateimodus `0600` neu an und überschreibt keine vorhandene Datei. Keine Dokumenttexte oder Parserausgaben in normalen CLI-Logs.
- Standardlimits: 15 MiB PDF, 20 Seiten, 1.500 normalisierte Blöcke, 45.000 extrahierte Zeichen und 600 Zellen je Tabelle. Worker: 6 GiB virtueller Adressraum, 110/115 CPU-Sekunden, 32 MiB je geschriebener Datei, 256 offene Dateien; JVM-Heap maximal 512 MiB. Für Dienste zusätzlich eine Host-/Container-Speichergrenze einrichten.
- `cancel` in `runner.extract` wird während eines Workers abgefragt. Es gibt einen Versuch je Parser; Fehler führen zu einem Fehlerergebnis, nicht zu einem anderen Anbieter.
- Keine OCR in diesem ersten Runner. Scans vorher lokal mit OCR vorbereiten. Analyseergebnisse einer vorhandenen OCR-/Docling-Vorbereitung können über `from_prepared` übernommen werden.

## Grenzen der Bewertung

Zwei übereinstimmende Parser können gemeinsam falsch liegen. Überdeckungs- und Textähnlichkeitswerte sind **keine kalibrierten Wahrscheinlichkeiten**. Split-/Merge-Fälle, komplexe Tabellen, seitenübergreifende Abschnittshierarchien, komplexe Schriftarten und gedrehte Seiten sind nicht umfassend aufgelöst. Tabellenzellen sind Kontextdaten; sie werden hier noch nicht automatisch an jeden separaten Übersetzungsblock angehängt.

Die Prüfplanung ist eine erste Vorauswahl. Die Bibliothek erzeugt keine Bildbeschreibungen und beurteilt keine Warnungsbedeutung. Der Zahlenvergleich ist konservativ und markiert auch geänderte Dezimalnotation; er ersetzt keine fachliche Übersetzungsprüfung.

Das PDF wird nicht umgeschrieben. Deshalb entsteht durch diese Bibliothek allein weder eine übersetzte Datei noch ein barrierefreies PDF. PDF/UA-Validierung, menschliche Prüfung und ein tatsächlicher Layoutvergleich gehören in die exportierende Anwendung. [veraPDF prüft nur maschinell prüfbare PDF/UA-Regeln](https://docs.verapdf.org/validation/).

## Lizenz und Quellen

Eigener Bibliothekscode: [MIT](LICENSE). Docling und OpenDataLoader sind separate Projekte mit eigenen Lizenzen; ihre Pakete und Modelle werden nicht in diesem Repository mitgeliefert.

- [Docling](https://github.com/docling-project/docling)
- [OpenDataLoader PDF](https://github.com/opendataloader-project/opendataloader-pdf)
- [OpenDataLoader-JSON-Schema](https://opendataloader.org/docs/reference/json-schema)
