Project Planning Toolkit

This repository contains Python scripts for generating key project management visuals — including Gantt charts, milestone timelines, and Work Breakdown Structure (WBS) diagrams — from simple CSV input files.

📦 Repository Contents
File	Purpose
.CSV files:
example_gantt.csv	Example input file for generating a Gantt chart and milestone timeline.
example_wbs.csv	Example input file for generating a hierarchical WBS diagram.
.py files:
main_gantt.py	Generates a Gantt chart from example_gantt.csv. (CSV path is set inside the script)
main_milestone.py	Creates a milestone timeline from example_gantt.csv. (CSV path is set inside the script)
main_wbs.py	Builds a hierarchical WBS diagram from example_wbs.csv. (Uses argparse for CSV and title input)

🚀 How to Use
Install dependencies:
pip install pandas matplotlib numpy
Correctly set input files in the script:
update the lines of the script needed to be used for the generation
Run the Gantt chart script:
python main_gantt.py


👉 The script will read the CSV path defined inside it (by default: example_gantt.csv) and generate a PNG and/or PDF output in the same directory.
Run the milestone timeline script:
python main_milestone.py


👉 Same as above — CSV path is defined in the script.
Run the WBS diagram script:
python main_wbs.py --csv example_wbs.csv --out wbs.png --title "Project Title"
(The WBS script supports command-line arguments for flexibility.)


📊 Input Format
WBS (example_wbs.csv)
ID	Title
1	Main Work Package
1.1	Sub Package
1.1.1	Detailed Task
Gantt & Milestones (example_gantt.csv)
ID	Task	Start	Finish	Group	Milestone	Dependencies
1	Kickoff	2026-01-01	2026-01-02	Phase A	TRUE	
2	Design	2026-01-03	2026-02-15	Phase B	FALSE	1

📊 Features
📆 Gantt Chart – timeline visualization of project tasks.
🎯 Milestone Timeline – key project events on a time axis.
🌳 WBS Diagram – hierarchical view of project structure.
📤 High-Quality Output – exports PNG and PDF for reports or presentations.

📌 Tips
Use dpi=300 for high-resolution images.
Prefer .pdf for scalable vector output.

✅ This toolkit helps you generate project visuals from simple CSV files — no proprietary project management software required.
