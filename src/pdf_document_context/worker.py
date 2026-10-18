"""Private worker entry point; intentionally no service, retries or cloud clients."""
import ctypes
import ctypes.util
import errno
import io
import json
from pathlib import Path
import resource
import sys


def isolate():
    # Filter survives exec(), also preventing JVM/third-party model connections.
    name = ctypes.util.find_library("seccomp")
    if not name:raise RuntimeError("libseccomp is required")
    lib = ctypes.CDLL(name, use_errno=True)
    lib.seccomp_init.argtypes = [ctypes.c_uint32]
    lib.seccomp_init.restype = ctypes.c_void_p
    lib.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    lib.seccomp_syscall_resolve_name.restype = ctypes.c_int
    lib.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint]
    lib.seccomp_load.argtypes = [ctypes.c_void_p]
    lib.seccomp_release.argtypes = [ctypes.c_void_p]
    ctx = lib.seccomp_init(0x7fff0000)  # ALLOW except listed syscalls
    if not ctx:raise RuntimeError("Cannot allocate network filter")
    try:
        for syscall in [b"connect", b"sendto", b"sendmsg", b"sendmmsg"]:
            number = lib.seccomp_syscall_resolve_name(syscall)
            if number < 0 or lib.seccomp_rule_add(ctx, 0x00050000 | errno.EPERM, number, 0) != 0:
                raise RuntimeError("Cannot configure network filter")
        if lib.seccomp_load(ctx) != 0:raise RuntimeError("Cannot activate network filter")
    finally:lib.seccomp_release(ctx)
    resource.setrlimit(resource.RLIMIT_CPU, (110, 115))
    resource.setrlimit(resource.RLIMIT_FSIZE, (32*1024**2,32*1024**2))
    resource.setrlimit(resource.RLIMIT_NOFILE, (256,256))
    resource.setrlimit(resource.RLIMIT_AS, (6*1024**3,6*1024**3))


def odl_options(request):
    options={"format":"json", "quiet":True, "image_output":"off", "include_header_footer":True}
    if request.get('include_hidden_text'):
        options['content_safety_off']=['hidden-text']
    return options


def main():
    request = json.loads(Path(sys.argv[1]).read_text())
    folder = Path(request["directory"])
    isolate()
    import importlib.metadata
    if request["engine"] == "opendataloader":
        import opendataloader_pdf
        # No hybrid, no AI backend, no images or tagged-PDF export.
        opendataloader_pdf.convert(input_path=[str(folder/"input.pdf")],
                                   output_dir=str(folder), **odl_options(request))
        output = folder/"input.json"
        if output.stat().st_size > request["max_json_bytes"]:raise ValueError("JSON too large")
        raw = json.loads(output.read_text())
        if int(raw["number of pages"]) > request["max_pages"]:raise ValueError("Too many pages")
    else:
        if not request["artifacts"]:raise ValueError("Preinstalled Docling artifacts required")
        from docling.datamodel.base_models import InputFormat, DocumentStream
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.datamodel.accelerator_options import AcceleratorOptions, AcceleratorDevice
        from docling.document_converter import DocumentConverter, PdfFormatOption
        options = PdfPipelineOptions(artifacts_path=Path(request["artifacts"]), do_ocr=False,
            do_table_structure=True, enable_remote_services=False, allow_external_plugins=False,
            document_timeout=85, do_picture_classification=False, do_picture_description=False,
            do_code_enrichment=False, do_formula_enrichment=False,
            accelerator_options=AcceleratorOptions(num_threads=2, device=AcceleratorDevice.CPU))
        converter = DocumentConverter(allowed_formats=[InputFormat.PDF],
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)})
        result = converter.convert(DocumentStream(name="input.pdf", stream=io.BytesIO((folder/"input.pdf").read_bytes())),
            max_num_pages=request["max_pages"], max_file_size=15*1024**2, raises_on_error=True)
        raw = result.document.export_to_dict()
    encoded = json.dumps({"version": importlib.metadata.version(
        "docling" if request["engine"] == "docling" else "opendataloader-pdf"), "data": raw}, ensure_ascii=False)
    if len(encoded.encode()) > request["max_json_bytes"]:raise ValueError("JSON too large")
    (folder/"result.json").write_text(encoded)


if __name__ == "__main__":
    main()
