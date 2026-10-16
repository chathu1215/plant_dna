"""
Plant DNA Identification System — Professional PDF Lab Report Generator
==========================================================================
Generates publication-quality, branded scientific laboratory reports in PDF format.
Includes institution header, plant photograph, comprehensive taxonomy,
botanical/pharmacological profile, and detailed color-annotated BLAST alignments.
"""

import os
import base64
from datetime import datetime
from typing import Dict, Any, List

from PyQt6.QtGui import QTextDocument, QPageLayout, QPageSize
from PyQt6.QtCore import QMarginsF
from PyQt6.QtPrintSupport import QPrinter

from database import get_field_value
from algorithms import chunk_alignment


def _get_image_base64_or_fallback(row: dict, images_dir: str) -> str:
    """Finds plant photo and converts to base64 data URI for flawless embedded printing."""
    raw_img = get_field_value(row, ['Plant Images', 'image', 'photo']) or ''
    sci_name = get_field_value(row, ['Scientific Name', 'name']) or ''

    img_path = None
    if raw_img and os.path.isabs(raw_img) and os.path.isfile(raw_img):
        img_path = raw_img
    elif raw_img and images_dir and os.path.isfile(os.path.join(images_dir, os.path.basename(raw_img))):
        img_path = os.path.join(images_dir, os.path.basename(raw_img))
    elif sci_name and images_dir:
        candidates = [
            os.path.join(images_dir, f"{sci_name}.jpg"),
            os.path.join(images_dir, f"{sci_name.lower().replace(' ', '_')}.jpg"),
            os.path.join(images_dir, f"{sci_name.lower().replace(' ', '')}.jpg"),
            os.path.join(images_dir, "messua_ferrea.jpg") if "mesua" in sci_name.lower() else None
        ]
        for c in candidates:
            if c and os.path.isfile(c):
                img_path = c
                break

    if img_path and os.path.isfile(img_path):
        try:
            with open(img_path, "rb") as img_f:
                b64_data = base64.b64encode(img_f.read()).decode("utf-8")
                ext = os.path.splitext(img_path)[1].lower().replace('.', '')
                mime = "image/png" if ext == "png" else "image/jpeg"
                return f"data:{mime};base64,{b64_data}"
        except Exception:
            pass

    return ""


def generate_plant_lab_report(row: Dict[str, Any], output_pdf_path: str, images_dir: str = "") -> bool:
    """
    Generates an official, publication-ready PDF laboratory report for a given plant record.
    Returns True on success, raises exception on failure.
    """
    sci_name = get_field_value(row, ['Scientific Name', 'name', 'ශාකයේ නම']) or 'Unknown Plant'
    common_name = get_field_value(row, ['Common Name', 'local name', 'පොදු නම']) or 'N/A'
    family = get_field_value(row, ['Family', 'කුලය']) or 'N/A'
    genus = get_field_value(row, ['Genus', 'ජීනසය']) or 'N/A'
    species = get_field_value(row, ['Species', 'විශේෂය']) or 'N/A'
    plant_type = get_field_value(row, ['Plant Type / Growth Form', 'Plant Type']) or 'N/A'
    description = get_field_value(row, ['Plant Description', 'description']) or 'N/A'
    morphology = get_field_value(row, ['Morphological Features', 'morphology']) or 'N/A'
    distribution = get_field_value(row, ['Distribution', 'distribution']) or 'N/A'
    habitat = get_field_value(row, ['Habitat', 'habitat']) or 'N/A'
    climate_soil = get_field_value(row, ['Climate & Soil Requirements', 'climate & soil']) or 'N/A'
    endemism = get_field_value(row, ['Endemism / Native Range', 'endemism']) or 'N/A'
    conservation = get_field_value(row, ['Conservation Status', 'conservation']) or 'N/A'
    uses = get_field_value(row, ['Uses', 'uses']) or 'N/A'
    traditional_uses = get_field_value(row, ['Traditional Uses (Sri Lanka)', 'traditional uses']) or 'N/A'
    phytochemicals = get_field_value(row, ['Key Phytochemicals', 'phytochemicals']) or 'N/A'
    pharmacological = get_field_value(row, ['Pharmacological Properties (Reported)', 'pharmacology']) or 'N/A'
    voucher_code = get_field_value(row, ['Voucher Specimen Code', 'voucher']) or 'N/A'

    has_dna_align = row.get('_has_dna_alignment', False)
    if has_dna_align:
        identity_str = get_field_value(row, ['Identity Percentage']) or f"{row.get('_identity_num', 0.0):.2f}%"
        matched_regions = row.get('_matched_regions', 'N/A')
    else:
        identity_str = "N/A (Taxonomic Query)"
        matched_regions = "None (Name Query)"

    e_val_num = row.get('_e_value', None)
    e_val_str = "0.0" if e_val_num == 0.0 else (f"{e_val_num:.2e}" if e_val_num is not None and e_val_num != float('inf') else "N/A")

    # Determine confidence status badge
    if not has_dna_align:
        verdict_badge = "<span style='background-color:#0f172a; color:#38bdf8; padding:4px 14px; border-radius:6px; font-weight:bold; font-size:10.5pt;'>TAXONOMIC MATCH</span>"
    elif e_val_num is not None and e_val_num < 1e-30:
        verdict_badge = "<span style='background-color:#0071e3; color:#ffffff; padding:4px 14px; border-radius:6px; font-weight:bold; font-size:10.5pt;'>CONFIRMED MATCH</span>"
    elif e_val_num is not None and e_val_num < 1e-10:
        verdict_badge = "<span style='background-color:#d97706; color:#ffffff; padding:4px 14px; border-radius:6px; font-weight:bold; font-size:10.5pt;'>PROBABLE MATCH</span>"
    else:
        verdict_badge = "<span style='background-color:#0f172a; color:#38bdf8; padding:4px 14px; border-radius:6px; font-weight:bold; font-size:10.5pt;'>REFERENCE RECORD</span>"

    # Image
    img_data_uri = _get_image_base64_or_fallback(row, images_dir)
    if img_data_uri:
        img_html = f"""
            <div style="text-align:center; margin-bottom:10px;">
                <img src="{img_data_uri}" width="180" height="180" style="border-radius:12px; border:2px solid #0a84ff; object-fit:cover;" />
                <div style="font-size:8.5pt; color:#64748b; font-style:italic; margin-top:4px;">Voucher Specimen: {voucher_code}</div>
            </div>
        """
    else:
        img_html = f"""
            <div style="text-align:center; padding:35px 20px; background-color:#f1f5f9; border-radius:12px; border:1px solid #cbd5e1; margin-bottom:10px;">
                <div style="font-size:36pt; margin-bottom:6px;">🌿</div>
                <div style="font-size:9.5pt; color:#475569; font-weight:bold;">Botanical Specimen</div>
                <div style="font-size:8.5pt; color:#64748b;">Code: {voucher_code}</div>
            </div>
        """

    # Format Alignments Section
    alignments_data = row.get('_alignments', [])
    if alignments_data:
        alignments_html = """
        <div style="margin-top:24px; border-top:2px solid #0071e3; padding-top:14px;">
            <h3 style="color:#0f172a; font-size:13pt; margin-bottom:10px;">🔬 BIOINFORMATIC SEQUENCE ALIGNMENT (BLAST VERIFICATION)</h3>
        """
        for a_item in alignments_data:
            reg_name = a_item.get("region", "Marker Alignment")
            align_obj = a_item.get("alignment", {})
            a_eval = a_item.get("e_value", 10.0)
            a_eval_str = "0.0" if a_eval == 0.0 else f"{a_eval:.2e}"
            a_id = align_obj.get("identity", 0.0)
            a_matches = align_obj.get("matches", 0)
            a_mismatches = align_obj.get("mismatches", 0)
            a_gaps = align_obj.get("gaps", 0)
            a_len = align_obj.get("align_len", 0)

            chunks = chunk_alignment(align_obj, chunk_size=60)
            alignment_text_lines = []
            for c in chunks:
                alignment_text_lines.append(f"Query   {c['q_start']:>5}  {c['query']}  {c['q_end']}")
                alignment_text_lines.append(f"              {c['middle']}")
                alignment_text_lines.append(f"Subject {c['s_start']:>5}  {c['subject']}  {c['s_end']}")
                alignment_text_lines.append("")

            formatted_seq_block = "\n".join(alignment_text_lines)

            alignments_html += f"""
            <div style="background-color:#f8fafc; border:1px solid #cbd5e1; border-radius:8px; padding:12px; margin-bottom:16px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:8px; border-bottom:1px solid #e2e8f0; padding-bottom:6px;">
                    <span style="font-size:11pt; font-weight:bold; color:#0f172a;">Region: {reg_name}</span>
                    <span style="font-size:10pt; color:#0071e3; font-weight:bold;">Identity: {a_id}% | E-value: {a_eval_str}</span>
                </div>
                <table style="width:100%; font-size:9pt; margin-bottom:8px; border-collapse:collapse;">
                    <tr>
                        <td style="padding:3px; color:#475569;"><b>Matches:</b> {a_matches}</td>
                        <td style="padding:3px; color:#475569;"><b>Mismatches:</b> {a_mismatches}</td>
                        <td style="padding:3px; color:#475569;"><b>Gaps:</b> {a_gaps}</td>
                        <td style="padding:3px; color:#475569;"><b>Alignment Length:</b> {a_len} bp</td>
                    </tr>
                </table>
                <div style="background-color:#0f172a; color:#e2e8f0; padding:12px; border-radius:6px; font-family:Courier New, monospace; font-size:8pt; white-space:pre; line-height:1.4;">{formatted_seq_block}</div>
            </div>
            """
        alignments_html += "</div>"
    else:
        alignments_html = """
        <div style="margin-top:24px; border-top:1px solid #cbd5e1; padding-top:14px;">
            <h3 style="color:#0f172a; font-size:11pt; margin-bottom:8px;">🔬 BIOINFORMATIC SEQUENCE ALIGNMENT STATUS</h3>
            <div style="background-color:#f8fafc; border:1px solid #cbd5e1; border-radius:8px; padding:12px; color:#475569; font-size:9pt; line-height:1.5;">
                ℹ️ <b>No DNA sequences (rbcL, matK, ITS) were queried for alignment.</b><br/>
                This botanical laboratory record was retrieved via taxonomic/scientific name lookup in the reference database.
            </div>
        </div>
        """

    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Complete Document HTML
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8"/>
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #1e293b;
                line-height: 1.45;
                font-size: 10pt;
            }}
            .header-table {{
                width: 100%;
                border-bottom: 3px solid #0071e3;
                padding-bottom: 12px;
                margin-bottom: 16px;
            }}
            .title-main {{
                color: #0f172a;
                font-size: 17pt;
                font-weight: 800;
                letter-spacing: -0.5px;
                margin: 0;
            }}
            .subtitle {{
                color: #0071e3;
                font-size: 9pt;
                font-weight: 700;
                letter-spacing: 1px;
                margin-top: 2px;
            }}
            .report-name {{
                font-size: 13pt;
                font-weight: 800;
                color: #1e293b;
                margin-top: 6px;
            }}
            .meta-box {{
                background-color: #f0f7ff;
                border: 1.5px solid #0071e3;
                border-radius: 8px;
                padding: 10px 14px;
                margin-bottom: 16px;
            }}
            .grid-table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 14px;
            }}
            .grid-table td {{
                vertical-align: top;
                padding: 5px 8px;
            }}
            .section-title {{
                color: #0f172a;
                font-size: 11pt;
                font-weight: 800;
                border-bottom: 1.5px solid #cbd5e1;
                padding-bottom: 4px;
                margin-top: 14px;
                margin-bottom: 8px;
            }}
            .info-card {{
                background-color: #f8fafc;
                border-left: 3px solid #0071e3;
                padding: 6px 10px;
                border-radius: 4px;
                margin-bottom: 6px;
                font-size: 9.5pt;
            }}
            .footer-table {{
                width: 100%;
                border-top: 1px solid #cbd5e1;
                margin-top: 28px;
                padding-top: 10px;
                font-size: 8.5pt;
                color: #64748b;
            }}
        </style>
    </head>
    <body>
        <!-- Header -->
        <table class="header-table">
            <tr>
                <td style="width:70%;">
                    <div class="subtitle">FACULTY OF TECHNOLOGY • UNIVERSITY OF RUHUNA</div>
                    <div class="title-main">DEPARTMENT OF BIOSYSTEMS TECHNOLOGY</div>
                    <div class="report-name">MOLECULAR PLANT DNA IDENTIFICATION &amp; BARCODE REPORT</div>
                </td>
                <td style="width:30%; text-align:right; vertical-align:middle;">
                    {verdict_badge}
                    <div style="font-size:8pt; color:#64748b; margin-top:6px;">Generated: {current_date}</div>
                </td>
            </tr>
        </table>

        <!-- Meta Summary Box -->
        <div class="meta-box">
            <table style="width:100%; font-size:9.5pt;">
                <tr>
                    <td style="width:25%;"><b>Scientific Query:</b></td>
                    <td style="width:35%; color:#0f2922; font-weight:bold;"><i>{sci_name}</i></td>
                    <td style="width:20%;"><b>Sequence Identity:</b></td>
                    <td style="width:20%; color:#059669; font-weight:bold;">{identity_str}</td>
                </tr>
                <tr>
                    <td><b>Common Name:</b></td>
                    <td>{common_name}</td>
                    <td><b>Statistical E-value:</b></td>
                    <td style="color:#0284c7; font-weight:bold;">{e_val_str}</td>
                </tr>
                <tr>
                    <td><b>Matched Region:</b></td>
                    <td>{matched_regions}</td>
                    <td><b>Voucher Code:</b></td>
                    <td>{voucher_code}</td>
                </tr>
            </table>
        </div>

        <!-- Specimen Overview (2 Columns: Image + Classification) -->
        <table class="grid-table">
            <tr>
                <td style="width:32%; vertical-align:top;">
                    {img_html}
                </td>
                <td style="width:68%; vertical-align:top; padding-left:14px;">
                    <div class="section-title">TAXONOMIC CLASSIFICATION</div>
                    <table style="width:100%; font-size:9.5pt; border-collapse:collapse;">
                        <tr><td style="padding:4px 0; color:#64748b; width:35%;"><b>Family:</b></td><td style="font-weight:bold;">{family}</td></tr>
                        <tr><td style="padding:4px 0; color:#64748b;"><b>Genus:</b></td><td style="font-weight:bold;">{genus}</td></tr>
                        <tr><td style="padding:4px 0; color:#64748b;"><b>Species:</b></td><td style="font-weight:bold;"><i>{species}</i></td></tr>
                        <tr><td style="padding:4px 0; color:#64748b;"><b>Growth Form:</b></td><td>{plant_type}</td></tr>
                        <tr><td style="padding:4px 0; color:#64748b;"><b>Conservation Status:</b></td><td>{conservation}</td></tr>
                        <tr><td style="padding:4px 0; color:#64748b;"><b>Endemism / Range:</b></td><td>{endemism}</td></tr>
                    </table>
                </td>
            </tr>
        </table>

        <!-- Botanical & Phytochemical Profile -->
        <div class="section-title">BOTANICAL &amp; PHARMACOLOGICAL PROFILE</div>
        <div class="info-card"><b>Plant Description:</b> {description}</div>
        <div class="info-card"><b>Morphological Features:</b> {morphology}</div>
        <div class="info-card"><b>Habitat &amp; Ecological Distribution:</b> {distribution} &bull; <i>{habitat}</i></div>
        <div class="info-card"><b>Climate &amp; Soil Requirements:</b> {climate_soil}</div>
        <div class="info-card"><b>Commercial &amp; General Uses:</b> {uses}</div>
        <div class="info-card"><b>Traditional Uses (Sri Lanka):</b> {traditional_uses}</div>
        <div class="info-card"><b>Key Phytochemical Constituents:</b> {phytochemicals}</div>
        {f'<div class="info-card"><b>Pharmacological Properties:</b> {pharmacological}</div>' if pharmacological != 'N/A' else ''}

        <!-- Alignments -->
        {alignments_html}

        <!-- Footer -->
        <table class="footer-table">
            <tr>
                <td style="width:65%;">
                    <b>Ruhuna BST Plant DNA Barcoding Laboratory</b><br/>
                    Verified against certified reference accession markers via global/local pairwise dynamic programming.<br/>
                    <i>This electronic report is certified by the Automated Bioinformatic Barcode System.</i>
                </td>
                <td style="width:35%; text-align:right; vertical-align:bottom;">
                    <div style="border-bottom:1px solid #475569; width:160px; margin-left:auto; margin-bottom:4px;"></div>
                    Authorized Bioinformatician / System
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    # Generate PDF using QPrinter & QTextDocument
    doc = QTextDocument()
    doc.setHtml(full_html)

    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(output_pdf_path)

    # A4 Page layout
    page_layout = QPageLayout(
        QPageSize(QPageSize.PageSizeId.A4),
        QPageLayout.Orientation.Portrait,
        QMarginsF(12, 12, 12, 12),
        QPageLayout.Unit.Millimeter
    )
    printer.setPageLayout(page_layout)

    doc.print(printer)
    return True
