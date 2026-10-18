"""Linux one-shot engine runner with bounded output, deadline and cancellation."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
from .model import Limits


class EngineError(RuntimeError):
    """Sanitized engine failure (never contains document contents)."""


def extract(pdf: bytes, engine: str, *, python=sys.executable, java_home=None,
            artifacts=None, temporary_root="/dev/shm", timeout=120, cancel=None,
            limits=Limits(), include_hidden_text=False):
    """Run one engine, no retries; workers deny outbound connect() via seccomp.

    Linux + libseccomp required. Install model files separately. Temporary PDFs
    and JSON use the supplied directory (default Linux RAM filesystem) and are
    removed on success, error or cancellation. Select a trusted Python executable.
    """
    if engine not in {"docling", "opendataloader"}:
        raise ValueError("Unknown engine")
    if not pdf.startswith(b"%PDF-") or len(pdf)>limits.max_input_bytes:
        raise ValueError("Invalid PDF or input byte limit exceeded")
    if not 0 < timeout <= 300:
        raise ValueError("Timeout must be in (0, 300]")
    if cancel and cancel():raise EngineError("Analysis cancelled")
    env = {"PATH": "/usr/bin:/bin", "HOME": "/nonexistent", "LANG": "C.UTF-8",
           "PYTHONPATH": str(Path(__file__).resolve().parent.parent),
           "PYTHONDONTWRITEBYTECODE": "1", "HF_HUB_OFFLINE": "1",
           "TRANSFORMERS_OFFLINE": "1", "HF_HUB_DISABLE_TELEMETRY": "1",
           "DO_NOT_TRACK": "1", "OMP_NUM_THREADS": "2", "MKL_NUM_THREADS": "2",
           "OPENBLAS_NUM_THREADS": "2", "TOKENIZERS_PARALLELISM": "false",
           "JAVA_TOOL_OPTIONS": "-Xmx512m -XX:ActiveProcessorCount=2 -XX:ReservedCodeCacheSize=64m -XX:CompressedClassSpaceSize=64m"}
    if java_home:
        env["JAVA_HOME"] = str(Path(java_home).resolve())
        env["PATH"] = env["JAVA_HOME"]+"/bin:"+env["PATH"]
    with tempfile.TemporaryDirectory(prefix="pdf-context-",dir=temporary_root) as folder:
        folder = Path(folder)
        (folder/"input.pdf").write_bytes(pdf)
        request = {"engine": engine, "directory": str(folder), "artifacts": str(Path(artifacts).resolve()) if artifacts else None,
                   "max_pages": limits.max_pages, "max_json_bytes": limits.max_json_bytes,
                   "include_hidden_text": bool(include_hidden_text)}
        (folder/"request.json").write_text(json.dumps(request))
        started = time.monotonic()
        with subprocess.Popen([str(python), "-B", "-m", "pdf_document_context.worker", str(folder/"request.json")],
                              env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL, start_new_session=True) as proc:
            try:
                while proc.poll() is None:
                    if cancel and cancel():raise EngineError("Analysis cancelled")
                    if time.monotonic()-started>timeout:raise EngineError("Analysis deadline exceeded")
                    time.sleep(.05)
                if proc.returncode:
                    raise EngineError("Local engine failed; check installed versions, offline models and resource limits")
            finally:
                try:os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:pass
                proc.wait()
        output = folder/"result.json"
        if not output.is_file() or output.stat().st_size > limits.max_json_bytes:
            raise EngineError("Missing engine result or JSON byte limit exceeded")
        return json.loads(output.read_text())
