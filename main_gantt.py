#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import date2num, DateFormatter, MonthLocator, WeekdayLocator
from datetime import timedelta
from matplotlib.patches import Patch

# ===== SETTINGS =====
CSV_FILE = "your_file_here.csv"              # 👈 your CSV filename
CSV_DELIMITER = ","                     # ";" if needed
CSV_ENCODING = "utf-8"                  # "utf-8-sig" or "latin-1" if issues
DATE_FORMAT_HINT = None                 # e.g. "%d/%m/%Y" if DD/MM/YYYY
PROJECT_START_DEFAULT = "2026-01-01"    # used if no dates provided
OUTPUT_PREFIX = "your_output_prefix"    # output PNG/PDF
LEGEND_PREFIX = "your_legend_prefix"    # legend PNG
BAR_HEIGHT = 0.6
BACKGROUND_ALPHA = 0.16
MILESTONE_BG = "#D3D3D3"
ARROW_COLOR = "#000000"
ARROW_WIDTH = 0.8
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

def split_dependencies(s) -> list:
    if pd.isna(s): return []
    parts = re.split(r"[,\;]", str(s))
    return [p.strip() for p in parts if p.strip()]

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
    if "Dependencies" not in df.columns:
        df["Dependencies"] = ""

    if "Start" in df.columns:
        df["Start"] = pd.to_datetime(df["Start"], errors="coerce", format=DATE_FORMAT_HINT)
    if "Finish" in df.columns:
        df["Finish"] = pd.to_datetime(df["Finish"], errors="coerce", format=DATE_FORMAT_HINT)

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

    df.loc[df["Milestone"] & df["Start"].notna(), "Finish"] = df.loc[df["Milestone"], "Start"]

    df = df.dropna(subset=["Task"])
    df = df.sort_values(by=["Start", "Finish", "Task"]).reset_index(drop=True)
    df["_Deps"] = df["Dependencies"].apply(split_dependencies)
    return df

def plot_gantt(df: pd.DataFrame, title="Project Gantt"):
    n = len(df)
    y = np.arange(n)

    # ✅ Color palette based on GROUP
    groups_in_order = list(dict.fromkeys(df["Group"].tolist()))
    cmap = plt.get_cmap("tab20")
    group_colors = {g: cmap(i % 20) for i, g in enumerate(groups_in_order)}
    default_color = "#66BB6A"

    fig, ax = plt.subplots(figsize=(40, max(6, n * 0.38)))

    start_min = df["Start"].min()
    finish_max = df["Finish"].max()
    full_left = date2num(start_min)
    full_width_days = max(1, (finish_max - start_min).days)

    id_index = {}
    for i, row in df.iterrows():
        if pd.notna(row["ID"]) and str(row["ID"]).strip():
            id_index[str(row["ID"]).strip()] = dict(
                y=i, start=row["Start"], finish=row["Finish"], milestone=bool(row["Milestone"])
            )

    # 1) Row background
    for i, row in df.iterrows():
        bg_color = MILESTONE_BG if row["Milestone"] else group_colors.get(row["Group"], default_color)
        ax.barh(
            y=i, width=full_width_days, left=full_left,
            height=BAR_HEIGHT * 1.8, color=bg_color, alpha=BACKGROUND_ALPHA, zorder=0
        )

    # 2) Bars & milestones
    for i, row in df.iterrows():
        start, finish = row["Start"], row["Finish"]
        color = group_colors.get(row["Group"], default_color)
        if row["Milestone"]:
            # ⬛ black diamond
            ax.scatter([date2num(start)], [i], marker="D", s=70, c="#000000", edgecolors="#000000", zorder=3)
            # ➕ milestone date label to the right of the diamond (kept inside x-limits)
            date_str = start.strftime("%Y-%m-%d")
            x_text = date2num(start) + 0.6  # shift ~0.6 day to the right
            xmax_num = date2num(finish_max) - 0.6
            if x_text > xmax_num:
                x_text = xmax_num
            ax.text(x_text, i, date_str, va="center", ha="left", fontsize=9, color="#000000", zorder=3)
        else:
            width = max(0.5, (finish - start).days)
            ax.barh(y=i, width=width, left=date2num(start), height=BAR_HEIGHT,
                    color=color, edgecolor="black", zorder=2)

    # 3) Dependencies (horizontal → vertical)
    for i, row in df.iterrows():
        curr_start = row["Start"]
        curr_y = i
        for dep in row["_Deps"]:
            pred = id_index.get(dep)
            if not pred:
                continue
            x0 = date2num(pred["finish"] if not pred["milestone"] else pred["start"])
            y0 = pred["y"]
            x1 = date2num(curr_start)
            y1 = curr_y
            ax.plot([x0, x1], [y0, y0], color=ARROW_COLOR, linewidth=ARROW_WIDTH, zorder=4)
            ax.annotate(
                "",
                xy=(x1, y1), xytext=(x1, y0),
                arrowprops=dict(arrowstyle="-|>", color=ARROW_COLOR, lw=ARROW_WIDTH, shrinkA=0, shrinkB=0),
                zorder=5
            )

    # Labels — two aligned columns: ID (right) and Task (right)
    ids = df["ID"].fillna("").astype(str)
    tasks = df["Task"].astype(str)
    max_id_len = ids.str.len().max()
    max_task_len = tasks.str.len().max()
    label_lines = [f"{id_:>{max_id_len}}   {task:>{max_task_len}}" for id_, task in zip(ids, tasks)]

    ax.set_yticks(y)
    ax.set_yticklabels(label_lines, fontsize=10, fontfamily="monospace")
    ax.invert_yaxis()

    # Column headers on the left (bold)
    header_id = "ID".rjust(max_id_len)
    header_task = "Task".rjust(max_task_len)
    ax.set_ylabel(f"{header_id}   {header_task}", fontsize=11, fontweight="bold", labelpad=15)

    # Timeline
    ax.xaxis.set_major_locator(MonthLocator(interval=1))
    ax.xaxis.set_major_formatter(DateFormatter("%b %Y"))
    ax.xaxis.set_minor_locator(WeekdayLocator(byweekday=0))
    ax.grid(True, which="major", axis="x", linestyle="--", alpha=0.4)
    ax.grid(True, which="minor", axis="x", linestyle=":", alpha=0.2)

    xmin = start_min - timedelta(days=3)
    xmax = finish_max + timedelta(days=7)
    ax.set_xlim([xmin, xmax])
    ax.set_title(title, fontsize=14, pad=12)
    ax.set_xlabel("Timeline")
    ax.set_ylabel("Tasks")

    fig.tight_layout()
    plt.savefig(f"{OUTPUT_PREFIX}.png", dpi=300, bbox_inches="tight")
    plt.savefig(f"{OUTPUT_PREFIX}.pdf", bbox_inches="tight")
    print(f"✅ Gantt chart saved as {OUTPUT_PREFIX}.png and {OUTPUT_PREFIX}.pdf")

    # ✅ Generate legend PNG
    generate_legend(group_colors)

def generate_legend(group_colors: dict):
    """Create a separate PNG with the group color legend sorted A→H→M and ONLY a milestone marker."""
    priority_order = ["A", "B", "C", "D", "E", "F", "G", "H", "M"]   # this part can be removed if not needed

    def priority_key(name: str):
        if not name or not isinstance(name, str):
            return 999
        first = name.strip()[0].upper()
        return priority_order.index(first) if first in priority_order else 998

    clean_group_colors = {k: v for k, v in group_colors.items() if str(k).strip().lower() != "milestone"}
    groups_sorted = sorted(clean_group_colors.keys(), key=lambda g: (priority_key(g), g))

    fig, ax = plt.subplots(figsize=(5, max(2, (len(groups_sorted) + 1) * 0.4)))  # +1 for milestone
    handles = [Patch(color=clean_group_colors[g], label=g) for g in groups_sorted if g]

    # Milestone legend entry (black diamond)
    milestone_handle = plt.Line2D(
        [0], [0],
        marker="D", color="w", markerfacecolor="#000000", markeredgecolor="#000000",
        markersize=10, linestyle="None", label="Milestone"
    )
    handles.append(milestone_handle)

    ax.legend(handles=handles, loc="center", fontsize=12, title="Main Packages Legend", frameon=False)
    ax.axis("off")

    fig.tight_layout()
    plt.savefig(f"{LEGEND_PREFIX}.png", dpi=200, bbox_inches="tight")
    print(f"✅ Legend saved as {LEGEND_PREFIX}.png (sorted A→H→M + milestone marker)")

if __name__ == "__main__":
    df = read_table(CSV_FILE)
    plot_gantt(df, title="your project title")
