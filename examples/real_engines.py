"""Opt-in end-to-end test. Requires PyMuPDF plus both installed engine runtimes.

Usage: python examples/real_engines.py --docling-python /path/to/python
       --odl-python /path/to/python --artifacts /path/to/models --java-home /path/to/jdk
No screenshots, actual user documents, cloud calls or reports are emitted.
"""
import argparse
import json
import fitz
from pdf_document_context import from_docling, from_opendataloader, reconcile, context_for
from pdf_document_context.runner import extract

parser=argparse.ArgumentParser()
parser.add_argument("--docling-python",required=True)
parser.add_argument("--odl-python",required=True)
parser.add_argument("--artifacts",required=True)
parser.add_argument("--java-home",required=True)
args=parser.parse_args()
pdf=fitz.open()
page=pdf.new_page(width=600,height=800)
page.insert_text((40,60),"Solar Repeller Basic",fontsize=18)
page.insert_text((40,100),"Read all instructions. Keep the device dry.",fontsize=11)
page.insert_text((40,125),"Use only 12 V power. Keep the Basic label.",fontsize=11)
page=pdf.new_page(width=600,height=800)
page.insert_text((40,50),"Technical specifications",fontsize=18)
for y in [100,130,160,190]:page.draw_line((40,y),(500,y))
for x in [40,270,500]:page.draw_line((x,100),(x,190))
for row,cells in enumerate([["Property","Value"],["Voltage","12 V"],["Power","5 W"]]):
    for col,text in enumerate(cells):page.insert_text((50+230*col,120+30*row),text,fontsize=11)
source=pdf.tobytes(no_new_id=True)
a=extract(source,"docling",python=args.docling_python,artifacts=args.artifacts)
b=extract(source,"opendataloader",python=args.odl_python,java_home=args.java_home)
first=from_docling(a["data"],a["version"])
second=from_opendataloader(b["data"],first.pages,b["version"])
merged=reconcile(first,second)
assert len(merged.pages)==2
assert "Solar Repeller Basic" in " ".join(x.text for x in merged.blocks)
assert any(x.cells for x in first.blocks),"Docling table missing"
assert any(x.cells for x in second.blocks),"OpenDataLoader table missing"
for item in merged.blocks:
    context=context_for(merged,item.id)
    assert len(json.dumps(context,ensure_ascii=False,separators=(",",":")))<=2400
assert pdf.tobytes(no_new_id=True)==source,"Analysis mutated the source PDF"
print(json.dumps({"versions":merged.engines,"pages":len(merged.pages),
    "primary_blocks":len(first.blocks),"secondary_blocks":len(second.blocks),
    "combined_blocks":len(merged.blocks),"blocks_with_issues":sum(bool(b.issues) for b in merged.blocks),
    "tables_both_engines":True,"bounded_contexts":True,"llm_calls":0}))
