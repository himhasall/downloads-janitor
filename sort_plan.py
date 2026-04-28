# sort_plan.py
# Downloads Folder Janitor — Session 2: Dry-Run Sorter
#
# Goal: look at every file in Downloads and decide WHERE it would go
# if we were sorting it — but don't actually move anything yet.
# This is a "dry run": all planning, zero action.
#
# In a later session we'll take this plan and execute it for real.

import sys
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Define the classification rules in one central dictionary.
#
# A dictionary (dict) maps keys to values, written as {key: value, ...}.
# Here each key is the name of a destination folder, and each value is a
# Python "set" of lowercase extensions that belong there.
#
# Why a set instead of a list?
#   Sets are optimised for membership testing ("is .jpg in here?").
#   The `in` operator on a set is much faster than scanning a list,
#   and sets automatically ignore duplicates — both nice properties.
#
# Why store everything here at the top?
#   So you only need to look in one place to add or change extensions.
#   For example, to start treating .webm as a video you'd add a new
#   "Videos" key — no hunting through the rest of the code required.
# ─────────────────────────────────────────────────────────────────────────────
EXTENSION_MAP = {
    "Photos":       {".jpg", ".jpeg", ".png", ".gif", ".heic",
                     ".webp", ".bmp", ".tiff", ".svg"},
    "PDFs":         {".pdf"},
    "Applications": {".exe", ".msi", ".dmg", ".pkg",
                     ".deb", ".rpm", ".appimage"},
    "Zips":         {".zip", ".rar", ".7z", ".tar", ".gz", ".tgz", ".bz2"},
    "Music":        {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".wma"},
}

# The five folder names we'll eventually create. We keep them in a set so
# we can quickly check "is this item one of our destination folders?"
# and skip it if so — they shouldn't appear in the plan.
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
# Same approach as list_files.py: Path.home() finds the current user's
# home directory without hardcoding any username, then / "Downloads"
# builds the full path using pathlib's path-joining operator.
# ─────────────────────────────────────────────────────────────────────────────
downloads = Path.home() / "Downloads"

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
