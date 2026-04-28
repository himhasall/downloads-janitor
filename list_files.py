# list_files.py
# Downloads Folder Janitor — Session 1: Read-Only Explorer
#
# Goal: Look inside your Downloads folder and describe what's there —
# without touching, moving, or changing anything.
# Think of this script as a flashlight, not a hand.

import sys
from pathlib import Path  # pathlib gives us a friendly, object-oriented way to work with file paths


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Find the Downloads folder
#
# Path.home() returns the current user's home directory (e.g. /Users/daksh).
# We join it with "Downloads" using the / operator — that's a pathlib trick
# where / means "join paths", not divide numbers.
# ─────────────────────────────────────────────────────────────────────────────
downloads = Path.home() / "Downloads"

# Guard clause: if the folder doesn't exist, tell the user clearly and stop.
# sys.exit(1) ends the program with error code 1 — the standard way to signal
# "something went wrong" to the terminal without printing a scary traceback.
if not downloads.exists():
    print(f"Error: Downloads folder not found at '{downloads}'")
    print("Please check that the path exists and try again.")
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — Define a helper function to convert raw bytes into a human-readable
#           size string (e.g. 1048576 → "1.0 MB").
#
# Computers store file sizes in bytes, but humans think in KB, MB, GB.
# We keep dividing by 1024 and stepping up the unit until the number is
# small enough to be readable. We stop at GB because that covers virtually
# all files you'll find in a Downloads folder.
# ─────────────────────────────────────────────────────────────────────────────
def format_size(size_in_bytes):
    """Return a human-readable file size string with one decimal place."""
    if size_in_bytes < 1024:
        return f"{size_in_bytes:.1f} B"
    elif size_in_bytes < 1024 ** 2:          # less than 1 MB
        return f"{size_in_bytes / 1024:.1f} KB"
    elif size_in_bytes < 1024 ** 3:          # less than 1 GB
        return f"{size_in_bytes / 1024 ** 2:.1f} MB"
    else:
        return f"{size_in_bytes / 1024 ** 3:.1f} GB"


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Iterate over the immediate contents of the Downloads folder.
#
# .iterdir() lists everything directly inside a folder — files AND subfolders —
# but does NOT go deeper into subfolders (no recursion). That's exactly what
# we want for this session: one layer only.
#
# We sort the results so the output is alphabetical and easy to read.
# ─────────────────────────────────────────────────────────────────────────────
file_count = 0    # we'll increment these as we loop
folder_count = 0

for item in sorted(downloads.iterdir()):

    # ── STEP 3a — Skip hidden files ──────────────────────────────────────────
    # On macOS and Linux, files whose names start with a dot (e.g. .DS_Store)
    # are hidden. They're system or app bookkeeping files — not interesting
    # for our janitor project, so we skip them with `continue`, which jumps
    # straight to the next item in the loop without doing anything else.
    if item.name.startswith("."):
        continue

    # ── STEP 3b — Decide if this item is a file or a directory ───────────────
    # pathlib gives us .is_dir() and .is_file() — simple True/False checks.
    # We use this to decide what label to print and how to show size/extension.
    if item.is_dir():
        item_type = "DIR"
        extension = "-"   # folders don't have a meaningful extension
        size_str  = "-"   # we won't try to measure a folder's total size
        folder_count += 1

    else:
        item_type = "FILE"
        # .suffix returns the last part of the filename after the final dot,
        # e.g. "report.pdf" → ".pdf". If there's no dot, suffix is "".
        extension = item.suffix if item.suffix else "-"

        # .stat() asks the operating system for metadata about the file.
        # .st_size is the file's size in bytes — this never opens the file itself.
        size_str = format_size(item.stat().st_size)
        file_count += 1

    # ── STEP 3c — Print one formatted line per item ──────────────────────────
    # We use an f-string to embed variables directly inside a string.
    # The format matches the spec exactly:
    #   [TYPE] filename | extension: .ext | size: X.X MB
    print(f"[{item_type}] {item.name} | extension: {extension} | size: {size_str}")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — Print the summary line.
#
# After the loop finishes, file_count and folder_count hold the totals.
# We print one final summary so the user gets a quick overview at a glance.
# ─────────────────────────────────────────────────────────────────────────────
print(f"\nTotal: {file_count} files, {folder_count} folders")
