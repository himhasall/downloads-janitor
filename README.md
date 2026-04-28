# Downloads Folder Janitor

A Python command-line tool that scans your Mac Downloads folder and sorts files into organised subfolders by type. Built as a learning project using only Python's standard library — no third-party packages required.

## Features

- Classifies files into 7 categories: Photos, PDFs, Applications, Zips, Music, Spreadsheets, AI Stuff
- Interactive y/n/q confirmation mode so you review each move before it happens
- `--auto` mode for unattended runs that moves everything without prompting
- Append-only audit log (`janitor_log.txt`) records every move with a timestamp
- Undo command that detects and reverses the most recent run
- Collision-safe: renames incoming files (e.g. `photo (1).jpg`) instead of overwriting

## How it works

| Script | What it does |
|---|---|
| `list_files.py` | Lists every file in Downloads with its type, extension, and size — read-only. |
| `sort_plan.py` | Classifies every file and previews where it would go — dry run, nothing moves. |
| `janitor.py` | Performs the actual moves, with confirmation prompts or `--auto` mode. |
| `undo_last_run.py` | Reads the log, identifies the last run, and reverses those moves. |

## Usage

Interactive mode — confirms each file before moving:
```
python3 janitor.py
```

Auto mode — moves all categorised files immediately, no prompts:
```
python3 janitor.py --auto
```

Undo last run — shows a preview and asks for confirmation before reversing:
```
python3 undo_last_run.py
```

Undo last run without confirmation prompt:
```
python3 undo_last_run.py --auto
```

## Requirements

- Python 3.6 or later
- Standard library only (`pathlib`, `shutil`, `argparse`, `datetime`) — nothing to install

## Built with

Built as a beginner Python learning project using the Antigravity IDE with Claude.
