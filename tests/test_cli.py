import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from pdf_document_context.cli import main


class CliTests(unittest.TestCase):
    def test_merge_report_is_private_and_not_logged(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            a={"pages":{"1":{"size":{"width":600,"height":800}}},
               "body":{"children":[{"label":"text","text":"Private fixture text", "prov":[
                   {"page_no":1,"bbox":{"l":40,"t":40,"r":400,"b":65,"coord_origin":"TOPLEFT"}}]}]}}
            b={"number of pages":1,"kids":[{"type":"paragraph","id":1,"page number":1,
                 "bounding box":[40,735,400,760],"content":"Private fixture text"}]}
            (folder/"a.json").write_text(json.dumps(a));(folder/"b.json").write_text(json.dumps(b))
            args=["pdf-document-context","merge",str(folder/"a.json"),str(folder/"b.json"),"--output",str(folder/"report.json")]
            stdout=io.StringIO()
            with patch("sys.argv",args),contextlib.redirect_stdout(stdout):main()
            report=json.loads((folder/"report.json").read_text())
            self.assertEqual(report["llm_calls"],0)
            self.assertFalse(report["pdfua_validated"])
            self.assertEqual((folder/"report.json").stat().st_mode & 0o777,0o600)
            self.assertNotIn("Private fixture text",stdout.getvalue())
            before=(folder/"report.json").read_bytes()
            with patch("sys.argv",args),contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):main()
            self.assertEqual((folder/"report.json").read_bytes(),before)

    def test_invalid_review_budget_rejected_before_execution(self):
        args=["pdf-document-context","analyze","nonexistent.pdf","--docling-artifacts","models","--output","missing.json","--max-review-requests","999"]
        with patch("sys.argv",args),contextlib.redirect_stderr(io.StringIO()),patch("pdf_document_context.cli.extract") as worker:
            with self.assertRaises(SystemExit):main()
            worker.assert_not_called()
