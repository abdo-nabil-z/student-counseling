"""
Turns a Template's Markdown+form-tag content into a final interactive PDF.

Owns everything specific to producing a PDF: the HTML/CSS page wrapper glued
around the template's own Markdown content, the Markdown->HTML conversion,
and the WeasyPrint/pyHanko layout + AcroForm field injection.

Template authors never write HTML or CSS themselves — `render_purpose_to_pdf`
calls `templates.rendering.render_with_wrapper` with this module's fixed
wrapper text, so the templates app stays entirely agnostic to what's being
wrapped.
"""
import io

import mistune
from weasyprint import HTML
from pyhanko.sign.fields import SigFieldSpec, append_signature_field
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.pdf_utils import generic as pdf_gen

from templates.rendering import render_with_wrapper

A4_WIDTH_PT = 595.28

# NOTE: the blank line before/after the Markdown body is required — it lets
# mistune (CommonMark HTML-block rules) pass this wrapper through untouched
# and convert only the template's own content in between.
HTML_HEAD = """<!DOCTYPE html><html><head>
<meta charset="utf-8">

<style>
@page {
  size: A4;
  margin: 60pt;
}

html, body { margin: 0; padding: 0; }
body   { font-family: Arial, sans-serif; font-size: 10pt; color: #111; }
h1     { font-size: 14pt; margin: 0 0 8pt; }
h2     { font-size: 11pt; margin: 18pt 0 4pt;
         border-bottom: 0.5pt solid #888; padding-bottom: 2pt; }
p      { margin: 4pt 0; line-height: 14pt; }
strong { font-weight: bold; }

table    { border-collapse: collapse; border-spacing: 0; width: 100%; margin: 8pt 0; }
th, td   { border: 0.75pt solid #000; padding: 3pt 6pt; text-align: left; }
th       { font-weight: bold; }

.tf-block    {
  margin-bottom: 10pt;
  /* keep the label glued to its field: never let a page break fall between
     them, and never split the field itself across two pages */
  break-inside: avoid-page;
  page-break-inside: avoid;
}
.tf-label    { font-weight: bold; margin-bottom: 3pt; font-size: 0.9em; }
.form-textfield {
  appearance: auto;
  width: 100%;
  box-sizing: border-box;
  font-family: inherit;
  font-size: inherit;
  border: 0.75pt solid #555;
  resize: none;
  display: block;
}

.inline-tf {
  appearance: auto;
  display: inline-block !important;
  width: 45%;
  min-width: 60pt;
  border: none;
  border-bottom: 0.75pt solid #333;
  background: transparent;
  font-family: inherit;
  font-size: inherit;
  padding: 0 2pt;
  vertical-align: baseline;
}

.inline-cb {
  appearance: auto;
  display: inline-block !important;
  width: 10pt;
  height: 10pt;
  vertical-align: middle;
  margin-right: 3pt;
  /* WeasyPrint's AcroForm click-rect is the content box only (no border/padding),
     so the visible outline must not add to the box size: outline draws without
     affecting layout, unlike border. */
  border: none;
  padding: 0;
  outline: 1px solid black;
}

.sig-block       {
  margin-bottom: 10pt;
  break-inside: avoid-page;
  page-break-inside: avoid;
}
.sig-placeholder {
  border: 1pt dashed #888;
  background: #fafafa;
  position: relative;
}
.sig-x {
  font-size: 18pt; color: #ccc;
  position: absolute; bottom: 4pt; left: 6pt;
}
</style>
</head><body>

"""

HTML_TAIL = """

</body></html>"""

_markdown = mistune.create_markdown(escape=False, plugins=["table"])


def _collect_sig_anchors(doc):
    """Walk WeasyPrint's rendered pages and collect anchors named sig_*, converted
    to PDF boxes (llx, lly, urx, ury) in pt, bottom-left origin."""
    results = []
    for page_idx, page in enumerate(doc.pages):
        scale = A4_WIDTH_PT / page.width
        page_h_pt = page.height * scale
        for anchor_id, bbox in page.anchors.items():
            if anchor_id.startswith("sig_"):
                x1, y1, x2, y2 = bbox
                field_name = anchor_id[len("sig_"):]
                llx = x1 * scale
                urx = x2 * scale
                ury = page_h_pt - y1 * scale
                lly = page_h_pt - y2 * scale
                results.append((field_name, page_idx, (llx, lly, urx, ury)))
    return results


def _inject_signatures(pdf_bytes: bytes, sig_anchors: list) -> bytes:
    if not sig_anchors:
        return pdf_bytes

    writer = IncrementalPdfFileWriter(io.BytesIO(pdf_bytes))
    for field_name, page_idx, box in sig_anchors:
        append_signature_field(
            writer,
            SigFieldSpec(sig_field_name=field_name, on_page=page_idx, box=box),
        )

    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def _inject_prefill(pdf_bytes: bytes, prefill: dict) -> bytes:
    if not prefill:
        return pdf_bytes

    writer = IncrementalPdfFileWriter(io.BytesIO(pdf_bytes))
    acroform = writer.root.get("/AcroForm")
    if acroform is None:
        return pdf_bytes

    def _walk(fields_array):
        for ref in fields_array:
            pdf_field = ref.get_object()
            t = pdf_field.get("/T")
            if t is not None:
                name = str(t)
                if name in prefill:
                    ft = pdf_field.get("/FT")
                    if ft == pdf_gen.NameObject("/Tx"):
                        pdf_field[pdf_gen.NameObject("/V")] = pdf_gen.pdf_string(str(prefill[name]))
                    elif ft == pdf_gen.NameObject("/Btn"):
                        state = pdf_gen.NameObject("/Yes") if prefill[name] else pdf_gen.NameObject("/Off")
                        pdf_field[pdf_gen.NameObject("/V")] = state
                        pdf_field[pdf_gen.NameObject("/AS")] = state
                    writer.mark_update(ref)
            kids = pdf_field.get("/Kids")
            if kids is not None:
                _walk(kids)

    _walk(acroform.get("/Fields", pdf_gen.ArrayObject()))
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def render_template_to_pdf(template_content: str, **context) -> bytes:
    """Full pipeline: Template.content (Markdown+form tags) -> interactive PDF bytes.

    Raises templates.rendering.TemplateRenderError on template errors, or
    whatever WeasyPrint/pyHanko raise on PDF generation errors.
    """
    result = render_with_wrapper(template_content, prepend=HTML_HEAD, append=HTML_TAIL, **context)
    html = _markdown(result.text)

    doc = HTML(string=html).render()
    sig_anchors = _collect_sig_anchors(doc)

    pdf_bytes = doc.write_pdf(pdf_forms=True)
    pdf_bytes = _inject_signatures(pdf_bytes, sig_anchors)

    if result.prefill:
        pdf_bytes = _inject_prefill(pdf_bytes, result.prefill)

    return pdf_bytes

