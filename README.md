# Project Planning Toolkit

Generate key project management visuals — **Gantt charts**, **milestone timelines**, and **Work Breakdown Structure (WBS) diagrams** — from simple CSV input files.

No proprietary project management software required.

---

## Repository Contents

### CSV Input Files

| File | Purpose |
|------|---------|
| `example_gantt.csv` | Example input for generating a Gantt chart and milestone timeline |
| `example_wbs.csv` | Example input for generating a hierarchical WBS diagram |

### Python Scripts

| File | Purpose |
|------|---------|
| `main_gantt.py` | Generates a Gantt chart from `example_gantt.csv` (CSV path is set inside the script) |
| `main_milestone.py` | Creates a milestone timeline from `example_gantt.csv` (CSV path is set inside the script) |
| `main_wbs.py` | Builds a hierarchical WBS diagram from `example_wbs.csv` (uses `argparse` for CSV and title input) |

---

## How to Use

### 1. Install dependencies

```bash
pip install pandas matplotlib numpy
```

### 2. Set input file paths

Update the CSV path inside each script as needed before running.

### 3. Run the scripts

**Gantt chart:**

```bash
python main_gantt.py
```

> The script reads the CSV path defined inside it (default: `example_gantt.csv`) and generates a PNG and/or PDF output in the same directory.

**Milestone timeline:**

```bash
python main_milestone.py
```

> Same as above — the CSV path is defined inside the script.

**WBS diagram:**

```bash
python main_wbs.py --csv example_wbs.csv --out wbs.png --title "Project Title"
```

> The WBS script supports command-line arguments for flexibility.

---

## Input Format

### WBS (`example_wbs.csv`)

| Column | Description |
|--------|-------------|
| `ID` | Unique identifier for each WBS element |
| `Title` | Name of the WBS element |

### Gantt & Milestones (`example_gantt.csv`)

| Column | Description |
|--------|-------------|
| `ID` | Unique task identifier |
| `Task` | Task name |
| `Start` | Start date |
| `Finish` | End date |
| `Group` | Grouping category |
| `Milestone` | Milestone flag |
| `Dependencies` | Task dependencies |

---

## Features

- **Gantt Chart** — Timeline visualization of project tasks
- **Milestone Timeline** — Key project events on a time axis
- **WBS Diagram** — Hierarchical view of project structure
- **High-Quality Output** — Exports PNG and PDF for reports or presentations

---

## Tips

- Use `dpi=300` for high-resolution images.
- Prefer `.pdf` for scalable vector output.

---

## License

MIT
