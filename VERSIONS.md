# Versionen und Kompatibilität

## 0.1.0

Erste experimentelle Veröffentlichung. Python-API und Datenformat können sich in späteren 0.x-Versionen ändern.

| Schnittstelle | Version / Nachweis |
|---|---|
| Bibliothek | `pdf-document-context==0.1.0` |
| Gemeinsames JSON-Datenformat | `1.0`, `Document.schema_version` |
| Primäradapter | Docling `2.140.0`, `DoclingDocument.export_to_dict()` |
| Zweitadapter | OpenDataLoader PDF `2.5.13`, `format="json"` |
| Einfacher Eingangsadapter | `pages` mit `width`, `height`, `items`; je Item `id`, `role`, `text`, `rect`, `order`, optional `cells` |
| Integrationslauf | Steuerung und OpenDataLoader unter Python 3.14, Docling unter Python 3.12, OpenJDK 21, CPU, vorinstallierte Docling-Modelle |
| Test-PDF-Erzeugung | PyMuPDF `1.26.7`; nicht Teil der Laufzeitabhängigkeiten |

Die optionale Abhängigkeitsgruppe `engines` pinnt die beiden Parser-Versionen. Transitive Abhängigkeiten und Modelldateien sind nicht vollständig gelockt; für reproduzierbare Produktivinstallationen zusätzlich eigene Plattform-Lockdatei und Modell-Prüfsummen führen. Ein bestandenes Beispiel ist keine allgemeine Qualitätszusage für beliebige PDFs.

Lokale Nachweise: 19 Tests jeweils unter Python 3.12 und 3.14. Der echte Zwei-Seiten-Lauf erkannte Tabellen mit beiden Parsern: fünf Primärblöcke, vier Zweitparser-Blöcke, sechs kombinierte Blöcke und drei offen markierte Unterschiede. Alle Kontexte blieben innerhalb der Grenze; keine LLM-Anfragen. Unterschiedliche Segmentierung wird absichtlich als offen ausgewiesen. Der Test überprüft keine PDF/UA-Konformität oder Übersetzungsqualität.

Beim Update eines Parsers: echten Text-/Tabellen-Test ausführen, Koordinatenkonvertierung prüfen, neue Ausgaben gegen bisherige Ergebnisse vergleichen und Versionsmatrix aktualisieren. Keine stillen Schemaanpassungen.
