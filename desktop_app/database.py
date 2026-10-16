"""
Plant DNA Identification System — Database Manager & Search Engine
=====================================================================
Handles CSV dataset loading, dynamic field retrieval, multi-marker weighted
alignment, and confidence statistical classification.
"""

import csv
import os
import re
from typing import List, Dict, Any, Optional

from algorithms import (
    needleman_wunsch,
    smith_waterman,
    get_reverse_complement,
    calculate_e_value
)


def load_database(csv_path: str) -> List[Dict[str, str]]:
    """
    Load the plant DNA barcoding CSV database. Returns list of row dictionaries.
    """
    if not os.path.isfile(csv_path):
        return []

    rows = []
    with open(csv_path, 'r', encoding='utf-8-sig', errors='replace') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip blank rows
            if any(str(v).strip() for v in row.values() if v is not None):
                # Clean header BOM and strip values
                cleaned_row = {
                    (k.replace('\ufeff', '').strip() if k else ''): (str(v).strip() if v is not None else '')
                    for k, v in row.items() if k
                }
                rows.append(cleaned_row)
    return rows


def get_field_value(row: Dict[str, str], possible_keys: List[str]) -> Optional[str]:
    """
    Dynamically extract a field from a CSV row by trying multiple key names.
    First tries exact match (case-insensitive), then substring match.
    """
    if not row:
        return None

    # Exact match pass
    for pk in possible_keys:
        for k, v in row.items():
            if k.strip().lower() == pk.strip().lower():
                if v and str(v).strip():
                    return str(v).strip()

    # Substring match pass (ignore internal keys starting with '_')
    for pk in possible_keys:
        for k, v in row.items():
            if k.startswith('_'):
                continue
            if pk.strip().lower() in k.strip().lower():
                if v and str(v).strip():
                    return str(v).strip()

    return None


def search_database(
    database: List[Dict[str, str]],
    scientific_name: str = "",
    rbcl_seq: str = "",
    matk_seq: str = "",
    its_seq: str = "",
    threshold: float = 70.0
) -> Dict[str, Any]:
    """
    Executes multi-marker bioinformatic search against the loaded dataset.
    Returns dictionary with:
      - 'results': sorted list of matching row dicts with alignment stats
      - 'verdict_type': 'confirmed' | 'probable' | 'weak' | 'info' | 'none'
      - 'verdict_message': formatted verdict message
      - 'top_e_value': lowest E-value found
    """
    sci_query = scientific_name.strip().upper()
    has_dna = bool(rbcl_seq or matk_seq or its_seq)

    matches = []

    for row in database:
        # Scientific/Common Name filtering
        if sci_query:
            val = get_field_value(row, [
                'Scientific Name', 'scientific name',
                'Common Name', 'common name',
                'Genus', 'Species', 'ශාකයේ නම'
            ])
            if not val or sci_query not in str(val).upper():
                continue

        # Multi-marker weighted scoring
        total_weight = 0.0
        weighted_identity_sum = 0.0
        best_e_value = float('inf')
        has_any_alignment = False
        matched_regions = []
        alignments_data = []

        marker_queries = [
            (rbcl_seq, ['DNA Sequence (rbcL)', 'dna sequence (rbcl)', 'rbcl', 'rbcL sequence', 'rbc-l'], 'rbcL', 40.0),
            (matk_seq, ['DNA Sequence (matK)', 'dna sequence (matk)', 'matk', 'matK sequence', 'mat-k'], 'matK', 40.0),
            (its_seq,  ['DNA Sequence (ITS)',  'dna sequence (its)',  'its',  'ITS sequence',  'its region'],  'ITS',  20.0),
        ]

        for query_seq, keys, label, weight in marker_queries:
            if not query_seq:
                continue

            total_weight += weight
            raw_target = get_field_value(row, keys) or ''
            target = re.sub(r'[^ATCGUNRYSWKMBDHV]', '', str(raw_target).upper())
            if not target:
                continue

            # Dual-strand alignment (Forward and Reverse Complement)
            def get_best_strand_alignment(q_seq, tgt):
                nw = needleman_wunsch(q_seq, tgt)
                if len(q_seq) < len(tgt) * 0.85 or nw['score'] <= 0:
                    sw = smith_waterman(q_seq, tgt)
                    if sw['score'] > nw['score']:
                        return sw
                return nw

            fwd_align = get_best_strand_alignment(query_seq, target)
            rev_query = get_reverse_complement(query_seq)
            rev_align = get_best_strand_alignment(rev_query, target)

            is_rev = rev_align['score'] > fwd_align['score']
            chosen_align = rev_align if is_rev else fwd_align
            display_label = f"{label} (RevComp)" if is_rev else label

            if chosen_align['align_len'] > 0:
                has_any_alignment = True
                matched_regions.append(display_label)
                weighted_identity_sum += chosen_align['identity'] * weight

                e_val = calculate_e_value(chosen_align['score'], chosen_align['q_len'], chosen_align['s_len'])
                if e_val < best_e_value:
                    best_e_value = e_val

                alignments_data.append({
                    "region": display_label,
                    "alignment": chosen_align,
                    "e_value": e_val
                })

        # If DNA markers were queried, we must have at least one valid alignment
        if has_dna and not has_any_alignment:
            continue

        row_copy = dict(row)
        row_copy['_has_dna_alignment'] = has_any_alignment
        row_copy['_alignments'] = alignments_data
        row_copy['_matched_regions'] = " + ".join(matched_regions) if matched_regions else "N/A"

        if has_any_alignment:
            final_identity = round(weighted_identity_sum / total_weight, 2) if total_weight > 0 else 0.0
            # Minimum identity cutoff filter
            if final_identity < threshold:
                continue
            row_copy['_identity_num'] = final_identity
            row_copy['_e_value'] = best_e_value
            row_copy['Identity Percentage'] = f"{final_identity:.2f}%"
            row_copy['Matched Barcode Region'] = row_copy['_matched_regions']
        else:
            row_copy['_identity_num'] = 0.0
            row_copy['_e_value'] = None
            row_copy['Identity Percentage'] = "N/A"
            row_copy['Matched Barcode Region'] = "N/A"

        matches.append(row_copy)

    # Sort results: descending identity if DNA search; alphabetically if name search
    if has_dna:
        matches.sort(key=lambda r: r['_identity_num'], reverse=True)
    else:
        def _get_name(r):
            v = get_field_value(r, ['Scientific Name', 'name', 'ශාකයේ නම']) or ''
            return str(v).lower()
        matches.sort(key=_get_name)

    # Statistical Verdict Banner Generation
    verdict_type = "none"
    verdict_msg = ""
    top_e = None

    if matches:
        if has_dna:
            top_hit = matches[0]
            top_e = top_hit.get('_e_value', float('inf'))
            p_name = get_field_value(top_hit, ['Scientific Name', 'name', 'ශාකයේ නම']) or 'Unknown Plant'
            formatted_e = "0.0" if top_e == 0.0 else f"{top_e:.2e}"

            if top_e < 1e-30:
                verdict_type = "confirmed"
                verdict_msg = (
                    f"Confirmed Match: Top hit is {p_name} with high statistical confidence "
                    f"(E-value: {formatted_e}, Identity: {top_hit['_identity_num']}%)."
                )
            elif top_e < 1e-10:
                verdict_type = "probable"
                verdict_msg = (
                    f"Probable Match: Top hit is {p_name} with moderate confidence "
                    f"(E-value: {formatted_e}, Identity: {top_hit['_identity_num']}%)."
                )
            else:
                verdict_type = "weak"
                verdict_msg = (
                    f"No Significant Match: Matches found are statistically weak "
                    f"(E-value: {formatted_e} > 1e-10) and likely random sequence noise."
                )
        else:
            verdict_type = "info"
            verdict_msg = (
                f"Taxonomic Name Query: Found {len(matches)} matching botanical record(s). "
                "No DNA sequences were queried for alignment."
            )

    return {
        "results": matches,
        "verdict_type": verdict_type,
        "verdict_message": verdict_msg,
        "top_e_value": top_e
    }
