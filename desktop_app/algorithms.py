"""
Plant DNA Identification System — Bioinformatics Alignment & Utility Engine
=============================================================================
Contains FASTA processing, IUPAC nucleotide validation, Reverse Complement generation,
Needleman-Wunsch Global Alignment, Smith-Waterman Local Alignment, and Karlin-Altschul
E-value statistical estimation.
"""

import math
from typing import Dict, Any, List, Tuple


def get_reverse_complement(seq: str) -> str:
    """
    Computes the reverse complement of a DNA sequence.
    Supports standard IUPAC degenerate bases (A, T, U, C, G, N, R, Y, S, W, K, M, B, D, H, V).
    """
    if not seq:
        return ""
    comp_map = {
        'A': 'T', 'T': 'A', 'U': 'A', 'C': 'G', 'G': 'C',
        'N': 'N', 'R': 'Y', 'Y': 'R', 'S': 'S', 'W': 'W',
        'K': 'M', 'M': 'K', 'B': 'V', 'V': 'B', 'D': 'H', 'H': 'D'
    }
    return "".join(comp_map.get(base, base) for base in reversed(seq.upper()))


def extract_dna_sequence(raw: str) -> Dict[str, Any]:
    """
    Strips FASTA definition headers (>...), coordinate numbers, and whitespace.
    Validates against IUPAC standard nucleotide codes: A, T, C, G, U, N, and degenerate bases.
    """
    if not raw or not isinstance(raw, str):
        return {"sequence": "", "is_valid": True, "invalid_chars": ""}

    lines = [line.strip() for line in raw.splitlines() if not line.strip().startswith('>')]
    joined = "".join(lines).upper()

    # Remove whitespace and numbers
    cleaned = "".join(ch for ch in joined if not ch.isspace() and not ch.isdigit())
    if not cleaned:
        return {"sequence": "", "is_valid": True, "invalid_chars": ""}

    valid_bases = set("ATCGUNRYSWKMBDHV-")
    invalid = [ch for ch in cleaned if ch not in valid_bases]

    if invalid:
        return {
            "sequence": "",
            "is_valid": False,
            "invalid_chars": "".join(sorted(list(set(invalid))))[:5]
        }

    return {
        "sequence": cleaned.replace('-', ''),
        "is_valid": True,
        "invalid_chars": ""
    }


def needleman_wunsch(seq1: str, seq2: str) -> Dict[str, Any]:
    """
    Needleman-Wunsch Global Alignment with N & Ambiguity support.
    Normalizes identity score by min(len1, len2) when score > 0 for coverage-aware accuracy.
    """
    MATCH = 2
    AMBIGUOUS_MATCH = 1
    MISMATCH = -1
    GAP = -2

    s1 = seq1[:2000]
    s2 = seq2[:2000]
    m, n = len(s1), len(s2)

    if m == 0 or n == 0:
        return {
            "a1": "", "a2": "", "middle": "",
            "matches": 0, "mismatches": 0, "gaps": 0,
            "align_len": 0, "identity": 0.0, "score": 0,
            "q_len": m, "s_len": n
        }

    def base_score(c1: str, c2: str) -> int:
        if c1 == c2:
            return MATCH
        if c1 == 'N' or c2 == 'N':
            return AMBIGUOUS_MATCH
        return MISMATCH

    # DP Matrix initialization
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i * GAP
    for j in range(n + 1):
        dp[0][j] = j * GAP

    # Filling Matrix
    for i in range(1, m + 1):
        c1 = s1[i - 1]
        for j in range(1, n + 1):
            c2 = s2[j - 1]
            score = base_score(c1, c2)
            dp[i][j] = max(
                dp[i - 1][j - 1] + score,
                dp[i - 1][j] + GAP,
                dp[i][j - 1] + GAP
            )

    # Traceback
    a1_list, a2_list, mid_list = [], [], []
    i, j = m, n
    while i > 0 or j > 0:
        c1 = s1[i - 1] if i > 0 else ''
        c2 = s2[j - 1] if j > 0 else ''
        score = base_score(c1, c2) if (i > 0 and j > 0) else MISMATCH

        if i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + score:
            a1_list.append(c1)
            a2_list.append(c2)
            if c1 == c2:
                mid_list.append('|')
            elif c1 == 'N' or c2 == 'N':
                mid_list.append(':')
            else:
                mid_list.append('.')
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + GAP:
            a1_list.append(c1)
            a2_list.append('-')
            mid_list.append(' ')
            i -= 1
        else:
            a1_list.append('-')
            a2_list.append(c2)
            mid_list.append(' ')
            j -= 1

    a1 = "".join(reversed(a1_list))
    a2 = "".join(reversed(a2_list))
    middle = "".join(reversed(mid_list))

    matches = 0
    mismatches = 0
    gaps = 0
    for k in range(len(a1)):
        if a1[k] == '-' or a2[k] == '-':
            gaps += 1
        elif a1[k] == a2[k] or a1[k] == 'N' or a2[k] == 'N':
            matches += 1
        else:
            mismatches += 1

    align_len = len(a1)
    if dp[m][n] > 0:
        eff_len = min(m, n)
        identity = round((matches / eff_len) * 100.0, 2)
    else:
        identity = round((matches / align_len) * 100.0, 2) if align_len > 0 else 0.0

    return {
        "a1": a1,
        "a2": a2,
        "middle": middle,
        "matches": matches,
        "mismatches": mismatches,
        "gaps": gaps,
        "align_len": align_len,
        "identity": identity,
        "score": dp[m][n],
        "q_len": m,
        "s_len": n
    }


def smith_waterman(seq1: str, seq2: str) -> Dict[str, Any]:
    """
    Smith-Waterman Local Alignment algorithm (optimal for partial sequence fragments).
    """
    MATCH = 2
    MISMATCH = -1
    GAP = -2

    s1 = seq1[:2000]
    s2 = seq2[:2000]
    m, n = len(s1), len(s2)

    if m == 0 or n == 0:
        return {
            "a1": "", "a2": "", "middle": "",
            "matches": 0, "mismatches": 0, "gaps": 0,
            "align_len": 0, "identity": 0.0, "score": 0,
            "q_len": m, "s_len": n
        }

    dp = [[0] * (n + 1) for _ in range(m + 1)]
    max_score = 0
    max_i, max_j = 0, 0

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            score = MATCH if s1[i - 1] == s2[j - 1] else MISMATCH
            val = max(
                0,
                dp[i - 1][j - 1] + score,
                dp[i - 1][j] + GAP,
                dp[i][j - 1] + GAP
            )
            dp[i][j] = val
            if val > max_score:
                max_score = val
                max_i, max_j = i, j

    a1_list, a2_list, mid_list = [], [], []
    i, j = max_i, max_j
    while i > 0 and j > 0 and dp[i][j] > 0:
        score = MATCH if s1[i - 1] == s2[j - 1] else MISMATCH
        if dp[i][j] == dp[i - 1][j - 1] + score:
            a1_list.append(s1[i - 1])
            a2_list.append(s2[j - 1])
            mid_list.append('|' if s1[i - 1] == s2[j - 1] else '.')
            i -= 1
            j -= 1
        elif dp[i][j] == dp[i - 1][j] + GAP:
            a1_list.append(s1[i - 1])
            a2_list.append('-')
            mid_list.append(' ')
            i -= 1
        else:
            a1_list.append('-')
            a2_list.append(s2[j - 1])
            mid_list.append(' ')
            j -= 1

    a1 = "".join(reversed(a1_list))
    a2 = "".join(reversed(a2_list))
    middle = "".join(reversed(mid_list))

    matches = 0
    mismatches = 0
    gaps = 0
    for k in range(len(a1)):
        if a1[k] == '-' or a2[k] == '-':
            gaps += 1
        elif a1[k] == a2[k]:
            matches += 1
        else:
            mismatches += 1

    align_len = len(a1)
    identity = round((matches / align_len) * 100.0, 2) if align_len > 0 else 0.0

    return {
        "a1": a1,
        "a2": a2,
        "middle": middle,
        "matches": matches,
        "mismatches": mismatches,
        "gaps": gaps,
        "align_len": align_len,
        "identity": identity,
        "score": max_score,
        "q_len": m,
        "s_len": n
    }


def calculate_e_value(score: float, m: int, n: int) -> float:
    """
    Computes statistical E-Value using Karlin-Altschul parameters (K=0.1, lambda=0.3).
    E = K * m * n * e^(-lambda * score)
    """
    if score <= 0 or m <= 0 or n <= 0:
        return 10.0

    K = 0.1
    lam = 0.3
    exponent = -lam * score
    if exponent < -500:
        return 0.0

    try:
        return K * m * n * math.exp(exponent)
    except OverflowError:
        return 0.0


def chunk_alignment(alignment: Dict[str, Any], chunk_size: int = 60) -> List[Dict[str, Any]]:
    """
    Splits alignment strings into fixed length visual chunks (default 60 bases per line)
    with accurate sequence coordinates.
    """
    a1 = alignment.get("a1", "")
    a2 = alignment.get("a2", "")
    middle = alignment.get("middle", "")

    chunks = []
    pos_q = 1
    pos_s = 1

    for i in range(0, len(a1), chunk_size):
        q_chunk = a1[i:i + chunk_size]
        m_chunk = middle[i:i + chunk_size]
        s_chunk = a2[i:i + chunk_size]

        q_bases = len(q_chunk.replace('-', ''))
        s_bases = len(s_chunk.replace('-', ''))

        q_end = pos_q + q_bases - 1 if q_bases > 0 else pos_q
        s_end = pos_s + s_bases - 1 if s_bases > 0 else pos_s

        chunks.append({
            "query": q_chunk,
            "middle": m_chunk,
            "subject": s_chunk,
            "q_start": pos_q,
            "q_end": q_end,
            "s_start": pos_s,
            "s_end": s_end
        })

        pos_q = q_end + 1
        pos_s = s_end + 1

    return chunks
