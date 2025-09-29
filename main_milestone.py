#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import textwrap
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, MonthLocator
from datetime import timedelta

# ===== SETTINGS =====
CSV_FILE = "example.csv"              # 👈 your CSV filename
CSV_DELIMITER = ","                     # ";" if needed
CSV_ENCODING = "utf-8"                  # "utf-8-sig" or "latin-1" if issues
DATE_FORMAT_HINT = None                 # e.g. "%d/%m/%Y" if DD/MM/YYYY
PROJECT_START_DEFAULT = "2026-01-01"    # used if no dates provided
OUTPUT_PREFIX = "your_output_prefix"    # output PNG/PDF

# Visuals
MARKER_COLOR = "#000000"
MARKER_SIZE = 80
LINE_COLOR = "#666666"
TEXT_FONTSIZE = 10
TITLE_FONTSIZE = 16

# Staggering: levels are vertical offsets from the center line (y=0)
# These repeat across milestones to reduce overlap.
LEVEL_SEQUENCE = [3, -3, 2, -2, 1, -1]  # tweak to your taste; add more entries for denser timelines
LEVEL_TEXT_GAP = 0.35  # extra gap between the connector tip and the first line of text

# Wrapping
MAX_LABEL_CHARS = 26  # ~characters per line for task names
MAX_LABEL_LINES = 3   # safety cap; extra text will be ellipsized
# ====================

CANON_MAP = {
    "id": "ID", "task": "Task", "activity": "Task", "activity description": "Task",
    "name": "Task", "duration": "Duration", "duration (days)": "Duration",
    "start": "Start", "start date": "Start", "finish": "Finish", "end": "Finish",
    "end date": "Finish", "group": "Group", "phase": "Group", "lane": "Group",
    "milestone": "Milestone", "dependencies": "Dependencies", "depends": "Dependencies",
    "predecessors": "Dependencies"
}

def normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    rename = {}
    for c in df.columns:
        key = str(c).strip().lower()
        rename[c] = CANON_MAP.get(key, c)
    return df.rename(columns=rename)

def parse_bool(x) -> bool:
    if pd.isna(x): return False
    s = str(x).strip().lower()
    return s in {"true", "1", "yes", "y"}

def read_table(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=CSV_DELIMITER, encoding=CSV_ENCODING)
    df = normalize_headers(df)

    if "Task" not in df.columns:
        raise KeyError("CSV must include a 'Task' column.")

    if "Group" not in df.columns:
        df["Group"] = "Default"
    if "ID" not in df.columns:
        df["ID"] = np.nan
    if "Milestone" not in df.columns:
        df["Milestone"] = False
    else:
        df["Milestone"] = df["Milestone"].apply(parse_bool)

    if "Start" in df.columns:
        df["Start"] = pd.to_datetime(df["Start"], errors="coerce", format=DATE_FORMAT_HINT)
    if "Finish" in df.columns:
        df["Finish"] = pd.to_datetime(df["Finish"], errors="coerce", format=DATE_FORMAT_HINT)

    # Fallback to duration if dates missing
    if (("Start" not in df.columns) or ("Finish" not in df.columns) or
        df["Start"].isna().any() or df["Finish"].isna().any()):
        if "Duration" not in df.columns:
            raise KeyError("Provide either Start+Finish or a Duration column.")
        proj_start = pd.to_datetime(PROJECT_START_DEFAULT)
        starts, finishes, current = [], [], proj_start
        for _, row in df.iterrows():
            d = row.get("Duration")
            d = float(d) if pd.notna(d) else 1.0
            s = current
            f = s + pd.to_timedelta(max(0.0, d), unit="D")
            starts.append(s); finishes.append(f); current = f
        if "Start" in df.columns:
            df["Start"] = df["Start"].fillna(pd.Series(starts, index=df.index))
        else:
            df["Start"] = starts
        if "Finish" in df.columns:
            df["Finish"] = df["Finish"].fillna(pd.Series(finishes, index=df.index))
        else:
            df["Finish"] = finishes

    # For milestones: use Start as date
    df.loc[df["Milestone"] & df["Start"].notna(), "Finish"] = df.loc[df["Milestone"], "Start"]

    return df.dropna(subset=["Task"]).reset_index(drop=True)

def wrap_text(s: str, width: int = MAX_LABEL_CHARS, max_lines: int = MAX_LABEL_LINES) -> str:
    """Wrap text to a fixed width and cap the number of lines (ellipsis overflow)."""
    if not s:
        return ""
    wrapped = textwrap.wrap(str(s), width=width, break_long_words=True, replace_whitespace=False)
    if len(wrapped) > max_lines:
        # Ellipsize the last line
        keep = wrapped[:max_lines]
        if len(keep[-1]) > 3:
            keep[-1] = keep[-1][:-3] + "..."
        else:
            keep[-1] = "..."
        wrapped = keep
    return "\n".join(wrapped)

from matplotlib.patches import Polygon
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.dates import date2num

def draw_center_gradient_arrow(ax, x0, x1, height=0.6):
    """
    Draw a green gradient arrow bar centered at y=0 with your custom shades.
    """
    # 🌿 Custom green palette
    fill_lvl1 = "#4ea72e"  # darkest (left)
    fill_lvl2 = "#d0e1cd"  # mid
    fill_lvl3 = "#e9f1e8"  # lightest (right)
    cmap = LinearSegmentedColormap.from_list("custom_green", [fill_lvl1, fill_lvl2, fill_lvl3])

    # Convert datetimes → numeric
    n0 = date2num(x0)
    n1 = date2num(x1)

    # Arrowhead width (≈3% of span, min ~5 days)
    span_days = max((x1 - x0).days, 1)
    head_w_days = max(span_days * 0.03, 5)
    head_w = head_w_days

    # Gradient rectangle (leaving space for arrowhead)
    rect_right = n1 - head_w
    grad = np.linspace(0, 1, 512).reshape(1, -1)
    ax.imshow(
        grad,
        extent=[n0, rect_right, -height, height],
        aspect="auto",
        cmap=cmap,
        interpolation="bicubic",
        zorder=0,
        origin="lower",
    )

    # Arrowhead polygon (using the lightest shade)
    head = Polygon(
        [(rect_right, -height), (rect_right, height), (n1, 0)],
        closed=True,
        facecolor=fill_lvl3,
        edgecolor="none",
        zorder=1,
    )
    ax.add_patch(head)

def plot_milestones(df: pd.DataFrame, title="Project Milestones"):
    # ✅ Only milestones
    milestones = df[df["Milestone"]].copy()
    if milestones.empty:
        raise ValueError("No milestones found in the CSV (Milestone=True).")

    milestones = milestones.sort_values("Start").reset_index(drop=True)

    dates = milestones["Start"].tolist()
    tasks = milestones["Task"].tolist()

    fig, ax = plt.subplots(figsize=(22, 7))

    # Timeline span
    start_min = min(dates) - timedelta(days=10)
    end_max   = max(dates) + timedelta(days=10)
    ax.set_xlim([start_min, end_max])
    draw_center_gradient_arrow(ax, start_min, end_max, height=0.6)

    # Build staggered levels
    seq = np.array(LEVEL_SEQUENCE, dtype=float)
    levels = np.tile(seq, int(np.ceil(len(dates) / len(seq))))[:len(dates)]

    for d, task, level in zip(dates, tasks, levels):
        # Milestone marker (diamond on center line)
        ax.scatter(d, 0, s=MARKER_SIZE, c=MARKER_COLOR, marker="D", zorder=3)

        # Connector line from center to label level
        ax.vlines(d, 0, level, color=LINE_COLOR, linewidth=1, zorder=2)

        # Where to place text
        va = "bottom" if level > 0 else "top"
        y_text = level + (LEVEL_TEXT_GAP if level > 0 else -LEVEL_TEXT_GAP)

        # Wrapped labels
        task_wrapped = wrap_text(task, width=MAX_LABEL_CHARS, max_lines=MAX_LABEL_LINES)
        date_str = d.strftime("%b %d, %Y")

        # Task (bold)
        ax.text(
            d, y_text,
            task_wrapped,
            ha="center", va=va, fontsize=TEXT_FONTSIZE, weight="bold",
            zorder=4, linespacing=1.15
        )
        # Date (a bit farther from connector)
        ax.text(
            d, y_text + (0.6 if level > 0 else -0.6),
            date_str,
            ha="center", va=va, fontsize=TEXT_FONTSIZE-1, color="#333333",
            zorder=4
        )

    # Axis formatting
    ax.xaxis.set_major_locator(MonthLocator(interval=1))
    ax.xaxis.set_major_formatter(DateFormatter("%b %Y"))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")

    ax.set_ylim(-(max(abs(seq)) + 1.5), (max(abs(seq)) + 1.5))
    ax.set_yticks([])
    ax.set_title(title, fontsize=TITLE_FONTSIZE, pad=20)
    ax.set_xlabel("Timeline")

    # Clean frame
    for spine in ("left", "right", "top"):
        ax.spines[spine].set_visible(False)

    fig.tight_layout()
    plt.savefig(f"{OUTPUT_PREFIX}.png", dpi=300, bbox_inches="tight")
    plt.savefig(f"{OUTPUT_PREFIX}.pdf", bbox_inches="tight")
    print(f"✅ Milestone chart saved as {OUTPUT_PREFIX}.png and {OUTPUT_PREFIX}.pdf")

if __name__ == "__main__":
    df = read_table(CSV_FILE)
    plot_milestones(df, title="your project title")
