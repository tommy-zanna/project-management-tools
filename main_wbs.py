#!/usr/bin/env python3
"""
make_wbs_png_big.py — Final version with:
- BIG boxes
- Real wrapping (top-left aligned)
- Consistent fonts & green gradient
- Correct WBS hierarchy structure
- ✅ Layer 0: Title box centered and connected to Level-1 packages
"""

import argparse
import pandas as pd
from textwrap import wrap
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
import matplotlib
matplotlib.use("Agg")


# --------------------------- Helpers ---------------------------

def detect_columns(df):
    id_col = title_col = None
    for c in df.columns:
        lc = c.strip().lower()
        if lc in {"id", "wbs_id", "wbs id", "number"}:
            id_col = c
        if lc in {"title", "task_name", "name", "description"}:
            title_col = c
    if not id_col or not title_col:
        raise RuntimeError("CSV must include ID and Title columns.")
    return id_col, title_col

def id_key(wbs):
    parts = str(wbs).split(".")
    out = []
    for p in parts:
        try:
            out.append(int(p))
        except:
            out.append(10**6)
    return tuple(out)

def build_hierarchy(df, id_col, title_col):
    nodes = {r[id_col]: r[title_col] for _, r in df.iterrows()}
    children = {k: [] for k in nodes}
    parent = {}
    for k in nodes:
        if "." in k:
            p = ".".join(k.split(".")[:-1])
            parent[k] = p
            children.setdefault(p, []).append(k)
        else:
            parent[k] = None
    for k in children:
        children[k].sort(key=id_key)
    top_levels = sorted([k for k, v in parent.items() if v is None], key=id_key)
    return nodes, children, top_levels

# --------------------------- Wrapping Helpers ---------------------------

def _px_from_points(points: float, dpi: float) -> float:
    return points * dpi / 72.0

def _text_width_px_textpath(s: str, fp: FontProperties, dpi: float) -> float:
    if not s:
        return 0.0
    tp = TextPath((0, 0), s, prop=fp)
    bb = tp.get_extents()
    return _px_from_points(bb.width, dpi)

# --------------------------- Drawing ---------------------------

def draw_box(ax, x_center, y_top, w, h, text, face, edge, lw,
             fontsize, max_lines=999, padding_x=90, padding_y=60, line_spacing=2):
    rect = Rectangle((x_center - w/2, y_top), w, h,
                     facecolor=face, edgecolor=edge, linewidth=lw, zorder=3)
    ax.add_patch(rect)

    dpi = ax.figure.dpi
    fp = FontProperties(size=fontsize)

    inner_w = max(1, (w - 2 * padding_x)*0.8)
    inner_h = max(1, h - 2 * padding_y)

    line_h_px = _px_from_points(fontsize, dpi) * line_spacing
    max_fit_lines = max(1, int(inner_h // line_h_px))
    if max_lines is not None:
        max_fit_lines = min(max_fit_lines, max_lines)

    words = str(text).split()
    lines = []
    current = ""

    def fits(s: str) -> bool:
        return _text_width_px_textpath(s, fp, dpi) <= inner_w

    i = 0
    n = len(words)
    while i < n and len(lines) < max_fit_lines:
        word = words[i]
        trial = (current + " " + word).strip() if current else word
        if fits(trial):
            current = trial
            i += 1
        else:
            if current == "":
                token = word
                lo, hi = 1, len(token)
                best = 1
                while lo <= hi:
                    mid = (lo + hi) // 2
                    if fits(token[:mid]):
                        best = mid
                        lo = mid + 1
                    else:
                        hi = mid - 1
                lines.append(token[:best])
                remainder = token[best:]
                if remainder:
                    words[i] = remainder
                else:
                    i += 1
            else:
                lines.append(current)
                current = ""
    if current and len(lines) < max_fit_lines:
        lines.append(current)

    if len(lines) > max_fit_lines:
        lines = lines[:max_fit_lines]
    truncated = (i < n) or (current and len(lines) == max_fit_lines)
    if truncated and lines:
        ell = "…"
        last = lines[-1]
        while not fits(last + ell) and last:
            last = last[:-1]
        lines[-1] = (last + ell) if last else ell

    x_text = (x_center - w/2) + padding_x
    y_text = y_top + padding_y
    for idx, line in enumerate(lines):
        ax.text(
            x_text,
            y_text + idx * line_h_px,
            line,
            ha="left",
            va="top",
            fontproperties=fp,
            zorder=4
        )

def vline(ax, x, y1, y2, lw=2.0):
    ax.plot([x, x], [y1, y2], linewidth=lw, color="#1b4332", zorder=1)

def hline(ax, x1, x2, y, lw=2.0):
    ax.plot([x1, x2], [y, y], linewidth=lw, color="#1b4332", zorder=1)

def estimate_height(root, children, box_h, lvl_gap_y, third_gap):
    y = box_h + lvl_gap_y
    for sec in children.get(root, []):
        y += box_h + lvl_gap_y
        thirds = children.get(sec, [])
        if thirds:
            y += third_gap + len(thirds) * (box_h + lvl_gap_y)
    return y + 400

# --------------------------- Main ---------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="Path to WBS CSV")
    ap.add_argument("--out", default="WBS_Tree_BIG.png", help="Output PNG path")
    ap.add_argument("--title", default="your default project title", help="Title text at top")
    ap.add_argument("--dpi", type=int, default=200)
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    id_col, title_col = detect_columns(df)
    df[id_col] = df[id_col].astype(str).str.strip()
    df[title_col] = df[title_col].astype(str).str.strip()
    df = df.sort_values(by=id_col, key=lambda s: s.map(id_key))

    nodes, children, top_levels = build_hierarchy(df, id_col, title_col)

    # --- Layout settings ---
    box_w = int(1100*1.2)
    box_h = int(600*1.2)
    col_gap = int(900 * 1.5)       # 1080
    lvl_gap_y = int(250 * 1.2)     # 300
    third_gap = int(300 * 1.2)     # 360
    indent_dx = int(700 * 1.2)     # 840
    spine_offset = int(60 * 1.2)

    font_lvl1 = 31
    font_lvl2 = 31
    font_lvl3 = 31

    edge_lvl0 = "#015c0b"
    edge_lvl1 = "#2d6a34"
    edge_lvl2 = "#409140"
    edge_lvl3 = "#94BB9D"

    fill_lvl0 = "#015c0b"
    fill_lvl1 = "#4ea72e"
    fill_lvl2 = "#d0e1cd"
    fill_lvl3 = "#e9f1e8"

    # --- Layer 0 (title box) settings ---
    title_w = 1600
    title_h = 420
    title_gap = 180
    title_font = 22

    col_heights = [estimate_height(r, children, box_h, lvl_gap_y, third_gap) for r in top_levels]
    fig_h = max(int(5500 * 1.2), int(max(col_heights) * 1.2))
    fig_w = max(int(12000 * 1.2), int(len(top_levels) * (box_w + col_gap) + col_gap))
    fig, ax = plt.subplots(figsize=(fig_w / args.dpi, fig_h / args.dpi), dpi=args.dpi)
    
    ax.set_xlim(0, fig_w)
    ax.set_ylim(fig_h, 0)
    ax.axis("off")

    # ---- Draw Layer 0 (title box) ----
    x_title = fig_w / 2
    y_title = 60
    draw_box(ax, x_title, y_title, title_w, title_h, args.title, fill_lvl1, edge_lvl1, 3, title_font)
    title_bottom = y_title + title_h
    y_start_cols = title_bottom + title_gap

    # ---- Draw each column ----
    for col_i, root in enumerate(top_levels):
        x_center = col_gap / 2 + col_i * (box_w + col_gap) + box_w / 2
        x_left = x_center - box_w / 2
        x_spine = x_left - spine_offset
        y = y_start_cols

        # Level 1 box
        draw_box(ax, x_center, y, box_w, box_h, f"{root} — {nodes[root]}", fill_lvl1, edge_lvl1, 3, font_lvl1)
        l1_mid_y = y + box_h / 2

        # Connect title to each Level-1 package
        vline(ax, x_title, title_bottom, l1_mid_y)
        hline(ax, x_title, x_spine, l1_mid_y)
        hline(ax, x_spine, x_left, l1_mid_y)

        y += box_h + lvl_gap_y
        sec_positions = []

        for sec in children.get(root, []):
            sec_positions.append(y + box_h / 2)
            draw_box(ax, x_center, y, box_w, box_h, f"{sec} — {nodes[sec]}", fill_lvl2, edge_lvl2, 2.5, font_lvl2)
            hline(ax, x_spine, x_left, y + box_h / 2)

            thirds = children.get(sec, [])
            y_next = y + box_h + lvl_gap_y

            if thirds:
                y_next += third_gap
                third_tops = [y_next + i * (box_h + lvl_gap_y) for i in range(len(thirds))]
                x_th_spine = x_center + indent_dx - box_w / 2 - 60

                sec_mid_y = y + box_h / 2
                hline(ax, x_left, x_th_spine, sec_mid_y)
                vline(ax, x_th_spine, sec_mid_y, third_tops[-1] + box_h + 30)
                vline(ax, x_th_spine, third_tops[0] - 30, third_tops[-1] + box_h + 30)

                for idx, th in enumerate(thirds):
                    top = third_tops[idx]
                    x_th_center = x_center + indent_dx
                    draw_box(ax, x_th_center, top, box_w, box_h,
                             f"{th} — {nodes[th]}", fill_lvl3, edge_lvl3, 2.5, font_lvl3)
                    hline(ax, x_th_spine, x_th_center - box_w / 2, top + box_h / 2)

                y_next = third_tops[-1] + box_h + lvl_gap_y

            y = y_next

        if sec_positions:
            vline(ax, x_spine, l1_mid_y, sec_positions[-1])

    plt.savefig(args.out, bbox_inches="tight")
    plt.savefig("WBS_Tree_BIG.pdf", dpi=800, bbox_inches="tight")  # specify the resolution based on the preferred image size
    print(f"✅ BIG WBS PNG saved to {args.out}")

if __name__ == "__main__":
    main()
