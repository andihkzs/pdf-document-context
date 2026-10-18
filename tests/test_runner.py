import errno
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from pdf_document_context.runner import extract, EngineError
from pdf_document_context.worker import odl_options


@unittest.skipUnless(sys.platform.startswith("linux"),"Linux runtime isolation")
class RunnerTests(unittest.TestCase):
    def test_image_extraction_disabled_and_ocr_layer_requires_explicit_opt_in(self):
        self.assertEqual(odl_options({})['image_output'],'off')
        self.assertNotIn('content_safety_off',odl_options({}))
        self.assertEqual(odl_options({'include_hidden_text':True})['content_safety_off'],['hidden-text'])

    def test_network_syscalls_denied(self):
        program="""from pdf_document_context.worker import isolate
import socket,errno
s=socket.socket()
isolate()
try:s.connect(('127.0.0.1',9))
except OSError as e:
 assert e.errno==errno.EPERM,e
 print('denied')
else:raise AssertionError('Connection allowed')
"""
        result=subprocess.run([sys.executable,"-c",program],capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout.strip(),"denied")

    def test_deadline_cancels_child_and_cleans_temp(self):
        with tempfile.TemporaryDirectory() as temp:
            helper=Path(temp)/"slow-python"
            helper.write_text('#!/bin/sh\nsleep 10\n');helper.chmod(0o700)
            start=time.monotonic()
            with self.assertRaisesRegex(EngineError,"deadline"):
                extract(b"%PDF-fixture","opendataloader",python=helper,temporary_root=temp,timeout=.15)
            self.assertLess(time.monotonic()-start,3)
            self.assertEqual(list(Path(temp).iterdir()),[helper])

    def test_cancellation_and_invalid_input(self):
        with self.assertRaisesRegex(EngineError,"cancelled"):
            extract(b"%PDF-fixture","docling",cancel=lambda:True)
        with self.assertRaises(ValueError):extract(b"not a PDF","docling")


if __name__=="__main__":unittest.main()
