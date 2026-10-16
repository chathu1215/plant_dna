"""
Plant DNA Identification System — BLAST-style Alignment Viewer Widget
========================================================================
Interactive widget displaying aligned nucleotide sequences with color-coded
matches, mismatches, gaps, coordinates, E-values, and identity progress bars.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QTextEdit, QProgressBar
)
from PyQt6.QtCore import Qt
from algorithms import chunk_alignment


class AlignmentViewerWidget(QFrame):
    def __init__(self, alignment_data: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("alignmentPanel")

        region_label = alignment_data.get("region", "DNA Alignment")
        align = alignment_data.get("alignment", {})
        e_val = alignment_data.get("e_value", 10.0)

        identity = align.get("identity", 0.0)
        matches = align.get("matches", 0)
        mismatches = align.get("mismatches", 0)
        gaps = align.get("gaps", 0)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Header Panel ──
        header_frame = QFrame()
        header_frame.setObjectName("alignmentHeader")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(14, 10, 14, 10)
        header_layout.setSpacing(12)

        title_lbl = QLabel(f"🧬 Alignment Viewer — {region_label}")
        title_lbl.setObjectName("alignmentHeaderText")
        header_layout.addWidget(title_lbl)

        header_layout.addStretch()

        # Stats badges
        e_val_str = "0.0" if e_val == 0.0 else f"{e_val:.2e}"
        stats_labels = [
            f"Identity: <b style='color:#58a6ff'>{identity}%</b>",
            f"E-value: <b style='color:#79c0ff'>{e_val_str}</b>",
            f"Matches: <b>{matches}</b>",
            f"Mismatches: <b>{mismatches}</b>",
            f"Gaps: <b>{gaps}</b>"
        ]

        for s_txt in stats_labels:
            badge = QLabel(s_txt)
            badge.setObjectName("alignmentStatBadge")
            header_layout.addWidget(badge)

        # Mini identity bar
        pbar = QProgressBar()
        pbar.setFixedSize(90, 16)
        pbar.setRange(0, 100)
        pbar.setValue(int(min(max(identity, 0), 100)))
        pbar.setTextVisible(False)
        header_layout.addWidget(pbar)

        main_layout.addWidget(header_frame)

        # ── Alignment Body (HTML Formatted) ──
        text_edit = QTextEdit()
        text_edit.setObjectName("alignmentText")
        text_edit.setReadOnly(True)
        text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Build color-coded HTML
        chunks = chunk_alignment(align, chunk_size=60)
        html_content = self._build_alignment_html(chunks)
        text_edit.setHtml(html_content)

        # Auto-adjust height based on number of chunks
        line_count = len(chunks) * 4 + 2
        text_edit.setMinimumHeight(min(max(line_count * 18, 120), 320))
        main_layout.addWidget(text_edit)

        # ── Legend ──
        legend_frame = QFrame()
        legend_frame.setStyleSheet("background-color:#161b22; padding:8px 16px; border-top:1px solid #30363d; border-bottom-left-radius:16px; border-bottom-right-radius:16px;")
        legend_layout = QHBoxLayout(legend_frame)
        legend_layout.setContentsMargins(10, 4, 10, 6)
        legend_layout.setSpacing(18)

        legend_items = [
            ("<span style='color:#58a6ff;'>■</span> Match (|)", "#8b949e"),
            ("<span style='color:#a5b4fc;'>■</span> Ambiguous (:)", "#8b949e"),
            ("<span style='color:#ff7b72;'>■</span> Mismatch (.)", "#8b949e"),
            ("<span style='color:#e3b341;'>■</span> Gap (–)", "#8b949e"),
        ]

        for symbol_html, color in legend_items:
            lbl = QLabel(symbol_html)
            lbl.setStyleSheet(f"font-size:11px; font-family:'SF Mono', 'Consolas'; color:{color};")
            legend_layout.addWidget(lbl)

        legend_layout.addStretch()
        main_layout.addWidget(legend_frame)

    def _build_alignment_html(self, chunks: list) -> str:
        html = [
            "<div style='font-family:SF Mono, Consolas, Courier New, monospace; font-size:12px; line-height:1.7; color:#f0f6fc; white-space:pre;'>"
        ]

        for c in chunks:
            q_seq = c["query"]
            m_seq = c["middle"]
            s_seq = c["subject"]

            q_colored = []
            s_colored = []
            m_colored = []

            for k in range(len(q_seq)):
                q_char = q_seq[k]
                s_char = s_seq[k]
                m_char = m_seq[k]

                if q_char == '-' or s_char == '-':
                    q_colored.append(f"<span style='color:#e3b341; font-weight:bold;'>{q_char}</span>")
                    s_colored.append(f"<span style='color:#e3b341; font-weight:bold;'>{s_char}</span>")
                    m_colored.append(f"<span style='color:#e3b341;'> </span>")
                elif q_char == s_char:
                    q_colored.append(f"<span style='color:#58a6ff; font-weight:bold;'>{q_char}</span>")
                    s_colored.append(f"<span style='color:#58a6ff; font-weight:bold;'>{s_char}</span>")
                    m_colored.append(f"<span style='color:#79c0ff;'>|</span>")
                elif q_char == 'N' or s_char == 'N' or m_char == ':':
                    q_colored.append(f"<span style='color:#a5b4fc; font-weight:bold;'>{q_char}</span>")
                    s_colored.append(f"<span style='color:#a5b4fc; font-weight:bold;'>{s_char}</span>")
                    m_colored.append(f"<span style='color:#a5b4fc;'>:</span>")
                else:
                    q_colored.append(f"<span style='color:#f87171; font-weight:bold; background-color:rgba(248,113,113,0.15);'>{q_char}</span>")
                    s_colored.append(f"<span style='color:#f87171; font-weight:bold; background-color:rgba(248,113,113,0.15);'>{s_char}</span>")
                    m_colored.append(f"<span style='color:#f87171;'>.</span>")

            q_str = "".join(q_colored)
            m_str = "".join(m_colored)
            s_str = "".join(s_colored)

            html.append(
                f"<div style='margin-bottom:12px;'>"
                f"<span style='color:#94a3b8;'>Query   {c['q_start']:>5}  </span>{q_str}<span style='color:#94a3b8;'>  {c['q_end']}</span><br/>"
                f"<span style='color:#64748b;'>              </span>{m_str}<br/>"
                f"<span style='color:#94a3b8;'>Subject {c['s_start']:>5}  </span>{s_str}<span style='color:#94a3b8;'>  {c['s_end']}</span>"
                f"</div>"
            )

        html.append("</div>")
        return "".join(html)
