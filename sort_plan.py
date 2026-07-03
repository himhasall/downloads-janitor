# sort_plan.py
# Downloads Folder Janitor — Session 2: Dry-Run Sorter
#
# Goal: look at every file in Downloads and decide WHERE it would go
# if we were sorting it — but don't actually move anything yet.
# This is a "dry run": all planning, zero action.
#
# In a later session we'll take this plan and execute it for real.

import sys
import json
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Load the classification rules from config.json.
#
# Beginners: the categories and file extensions this dry-run uses all live in
# config.json, NOT in this script. Open config.json in any text editor to add
# extensions or whole new categories without touching a single line of Python.
# janitor.py reads the very same file, so the plan you see here always matches
# what an actual clean-up would do.
#
# config.json must sit next to this script. We load it once at startup and
# bail out cleanly (no scary traceback) if it's missing, malformed, or
# missing a required key.
#
# Each category's extensions are stored as a JSON list; we convert them to a
# Python "set" because sets are optimised for membership testing ("is .jpg in
# here?") — the `in` operator on a set is much faster than scanning a list.
# ─────────────────────────────────────────────────────────────────────────────
config_path = Path(__file__).parent / "config.json"

if not config_path.exists():
    print("config.json not found in project folder. Please ensure it's present alongside the script.")
    sys.exit(1)

try:
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
except json.JSONDecodeError as error:
    print(f"config.json has invalid JSON. Error: {error}. Please check the file for syntax errors.")
    sys.exit(1)

for required_key in ("downloads_path", "categories", "skip_empty_folders"):
    if required_key not in config:
        print(f"config.json is missing required key: '{required_key}'. Please check the file.")
        sys.exit(1)

EXTENSION_MAP = {name: set(exts) for name, exts in config["categories"].items()}

# The folder names we'd eventually create. We keep them in a set so we can
# quickly check "is this item one of our destination folders?" and skip it if
# so — they shouldn't appear in the plan.
DESTINATION_FOLDERS = set(EXTENSION_MAP.keys())   # {'Photos', 'PDFs', ...}


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — Define a helper function that classifies a single file.
#
# Giving this logic its own function keeps the main loop clean and readable.
# The function takes a Path object and returns either a folder name like
# "Photos" or the string "SKIP" if no category matches.
#
# How the lookup works:
#   1. Grab the file's extension with .suffix  →  e.g. ".PDF"
#   2. Lowercase it with .lower()              →  ".pdf"
#      (so ".PDF", ".Pdf", ".pdf" all match the same rule)
#   3. Walk through every category in EXTENSION_MAP and ask
#      "is this extension in that category's set?"
#   4. Return the first category that says yes, or "SKIP" if none does.
# ─────────────────────────────────────────────────────────────────────────────
def classify(file_path):
    """Return the destination folder name for a file, or 'SKIP'."""
    ext = file_path.suffix.lower()   # e.g. ".PDF" → ".pdf"

    for folder_name, extensions in EXTENSION_MAP.items():
        if ext in extensions:
            return folder_name   # found a match — return immediately

    return "SKIP"   # no category claimed this extension


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Locate the Downloads folder.
#
# The location comes from config.json ("downloads_path"). We call .expanduser()
# so a leading "~" is expanded to your home folder correctly — this keeps the
# dry-run pointed at wherever janitor.py is configured to work.
# ─────────────────────────────────────────────────────────────────────────────
downloads = Path(config["downloads_path"]).expanduser()

if not downloads.exists():
    print(f"Error: Downloads folder not found at '{downloads}'")
    print("Please check that the path exists and try again.")
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — Set up counters to track how many files land in each category.
#
# dict.fromkeys(iterable, default) builds a new dict where every key from
# the iterable gets the same starting value. This is neater than writing
# {"Photos": 0, "PDFs": 0, ...} by hand — if you add a category to
# EXTENSION_MAP above, this counter dict automatically grows with it.
#
# We also add a "SKIP" counter for files that don't match any category.
# ─────────────────────────────────────────────────────────────────────────────
counts = dict.fromkeys(EXTENSION_MAP.keys(), 0)   # {"Photos": 0, "PDFs": 0, ...}
counts["SKIP"] = 0
total_files = 0


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — Walk through Downloads and print the plan for each item.
#
# .iterdir() yields every item directly inside the folder (no recursion —
# we deliberately don't go into subfolders). We sort the results so the
# output is alphabetical and easy to scan.
#
# For each item we apply three filters before doing anything else:
#   • Hidden files  — names starting with "." are system/app bookkeeping files.
#   • Directories   — we only classify files, not folders.
#   • Destination folders — if Photos/, PDFs/, etc. already exist in
#                           Downloads (from a previous run), skip them so they
#                           don't appear as uncategorised directories.
# ─────────────────────────────────────────────────────────────────────────────
for item in sorted(downloads.iterdir()):

    # Skip hidden files (e.g. .DS_Store, .localized)
    if item.name.startswith("."):
        continue

    # Skip directories — including our own destination folders if they
    # already exist. item.name checks just the final component of the path.
    if item.is_dir():
        if item.name in DESTINATION_FOLDERS:
            continue   # silently ignore our own target folders
        # For any other directory, also skip — we only classify files.
        continue

    # ── STEP 5a — Classify the file and increment the right counter ──────────
    # classify() does all the extension matching and returns a category string.
    # We then use that string as a key into our counts dict to keep score.
    category = classify(item)
    counts[category] += 1
    total_files += 1

    # ── STEP 5b — Print the plan line ────────────────────────────────────────
    # We use an f-string with left-alignment to make the arrow column line up
    # regardless of filename length. The format is:
    #   filename.ext  ->  Photos/
    # For SKIP files, we add a parenthetical note so it's clear why they're
    # being skipped and not silently dropped.
    if category == "SKIP":
        print(f"  {item.name}  ->  SKIP (no matching category)")
    else:
        print(f"  {item.name}  ->  {category}/")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — Print the summary block.
#
# After the loop, counts holds the final tally for every category.
# We print each one in the same order as EXTENSION_MAP (Python dicts
# preserve insertion order since Python 3.7), then SKIP, then the total.
#
# The "--- Summary ---" header visually separates the plan lines above
# from the aggregated totals below, so the output is easy to read at a glance.
# ─────────────────────────────────────────────────────────────────────────────
print("\n--- Summary ---")
for folder_name in EXTENSION_MAP:          # iterates keys in insertion order
    print(f"  {folder_name}: {counts[folder_name]}")
print(f"  SKIP: {counts['SKIP']}")
print(f"  Total: {total_files} files")
