# undo_last_run.py
# Downloads Folder Janitor — Session 4: Undo Last Run
#
# Goal: read janitor_log.txt and reverse ONLY the most recent batch of moves.
# "Most recent batch" = the contiguous block of log lines at the bottom of the
# file whose timestamps are all within 10 minutes of each other.
#
# We never touch files that aren't exactly where the log says they should be.
# We never overwrite anything. One failure never kills the whole run.
#
# New concepts introduced in this session:
#   • Reading a file backwards (reversed + splitlines)
#   • datetime.strptime  — parse a timestamp string into a datetime object
#   • timedelta          — represent a span of time and compare gaps
#   • Sentinel returns   — a function that returns None to mean "something's wrong"

import sys
import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta


# ─────────────────────────────────────────────────────────────────────────────
# STEP 0 — Load settings from config.json.
#
# Beginners: the categories and Downloads location this project uses live in
# config.json, NOT in this script — edit that file to customise things without
# touching any Python. Undo works entirely from the log file (janitor_log.txt),
# so it doesn't need the category list, but we load config.json here so it uses
# the SAME configured Downloads folder as janitor.py — keeping everything
# consistent wherever you've pointed "downloads_path".
#
# config.json must sit next to this script. We load it once at startup and
# bail out cleanly (no scary traceback) if it's missing, malformed, or
# missing a required key.
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

# The configured Downloads folder, with any leading "~" expanded to your home
# directory. Undo reads exact paths from the log, so this is kept for
# consistency with janitor.py rather than used to rebuild paths.
downloads = Path(config["downloads_path"]).expanduser()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Key paths.
#
# Path(__file__).parent gives the folder that contains THIS script — the
# workspace. The log file lives in that same folder, so we build its path
# the same way. This works regardless of where Python is run from.
# ─────────────────────────────────────────────────────────────────────────────
log_path = Path(__file__).parent / "janitor_log.txt"


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — Define the 10-minute window that separates runs.
#
# timedelta is a Python object that stores a duration (hours, minutes, seconds).
# Here it represents exactly 10 minutes. Later we'll subtract two datetime
# objects and compare the result against this constant.
#
# Using a named constant at the top (rather than a magic number like 600 buried
# in the code) makes the intent crystal-clear and easy to change in one place.
# ─────────────────────────────────────────────────────────────────────────────
RUN_WINDOW = timedelta(minutes=10)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Helper: parse one log line into structured data.
#
# Expected format for a move line:
#   "2026-04-25 14:32:01 | /old/full/path -> /new/full/path"
#
# Returns:
#   (datetime, Path, Path)   for a valid move line
#   "UNDO_MARKER"            for a previous undo marker — signals "stop here"
#   None                     for anything we should skip (errors, malformed, empty)
#
# Why return None instead of raising an exception?
# Because a malformed line is a nuisance, not a catastrophe — we want to skip
# it and keep going. Returning None lets the caller make that decision cleanly.
# ─────────────────────────────────────────────────────────────────────────────
def parse_line(line):
    """Parse one log line. Returns a tuple, 'UNDO_MARKER', or None."""
    line = line.strip()
    if not line:
        return None   # blank line — nothing to do

    # Split on " | " into at most two parts.
    # maxsplit=1 protects against paths that happen to contain " | ".
    parts = line.split(" | ", maxsplit=1)
    if len(parts) != 2:
        return None   # missing separator — malformed

    ts_str, rest = parts

    # Detect UNDO marker lines (written by a previous undo run).
    # They look like: "2026-04-25 14:40:00 | --- UNDO RUN: reversed 12 moves ---"
    # Hitting one means every line BEFORE it was already undone — stop collecting.
    if rest.startswith("---"):
        return "UNDO_MARKER"

    # Detect ERROR lines written by janitor.py — nothing to undo here.
    if rest.startswith("ERROR"):
        return None

    # Parse the timestamp string into a datetime object.
    # strptime (string parse time) is the reverse of strftime (string format time).
    # The format codes must match exactly what janitor.py wrote.
    try:
        ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None   # timestamp format didn't match — malformed line

    # Split the path portion on " -> " to extract old and new paths.
    if " -> " not in rest:
        return None   # missing arrow — malformed

    old_str, new_str = rest.split(" -> ", maxsplit=1)
    return (ts, Path(old_str.strip()), Path(new_str.strip()))


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — Check that the log file exists and has content.
#
# We handle both "file missing" and "file empty" the same way — print a clear
# message and exit with code 0 (0 means success / nothing wrong happened).
# ─────────────────────────────────────────────────────────────────────────────
if not log_path.exists():
    print("Nothing to undo.")
    sys.exit(0)

raw_lines = log_path.read_text(encoding="utf-8").splitlines()
if not raw_lines:
    print("Nothing to undo.")
    sys.exit(0)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — Walk backwards through the log to find the "last run".
#
# reversed(raw_lines) gives us the lines in bottom-to-top order without
# making a copy of the whole list — it's memory-efficient.
#
# Rules while walking backwards:
#   1. Skip blank lines, error lines, and malformed lines.
#   2. If we hit an UNDO marker → stop. Lines before it were already reversed.
#   3. The very first valid move we find anchors the run (prev_ts = its timestamp).
#   4. Each subsequent line must be within RUN_WINDOW of the line immediately
#      after it (prev_ts). If the gap is larger → stop, we've crossed a boundary.
#
# We build last_run in reverse-chronological order (newest first), then flip
# it at the end so we undo oldest-first — the safest order.
# ─────────────────────────────────────────────────────────────────────────────
last_run = []   # list of (timestamp, old_path, new_path) tuples
prev_ts  = None # timestamp of the most recently accepted line (the "anchor")

for line in reversed(raw_lines):
    parsed = parse_line(line)

    if parsed is None:
        # Blank, error, or malformed — skip without affecting the run boundary.
        continue

    if parsed == "UNDO_MARKER":
        # Explicit boundary: a previous undo run ended here.
        # Everything before this marker is already undone — stop collecting.
        break

    ts, old_path, new_path = parsed

    if prev_ts is None:
        # First valid move found — anchor the run and accept it unconditionally.
        prev_ts = ts
        last_run.append((ts, old_path, new_path))
        continue

    # Compare this line's timestamp against the line immediately after it.
    # Since we're walking backwards, prev_ts > ts, so the gap is prev_ts - ts.
    gap = prev_ts - ts
    if gap > RUN_WINDOW:
        # More than 10 minutes of silence between these two lines.
        # This is the boundary between two separate janitor runs — stop here.
        break

    # Still within the same run — accept this line and update the anchor.
    prev_ts = ts
    last_run.append((ts, old_path, new_path))

# If we found nothing to undo (log has only markers/errors), bail out cleanly.
if not last_run:
    print("Nothing to undo.")
    sys.exit(0)

# Flip from "newest first" → "oldest first" so the undo order mirrors the
# original move order in reverse. This is the least surprising sequence for
# the user and avoids any edge cases where File B depended on File A moving first.
last_run.reverse()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — Show the user a preview and ask for confirmation.
#
# We never do anything destructive without an explicit "y" from the user.
# Showing the time range lets them verify they're undoing the right session.
# ─────────────────────────────────────────────────────────────────────────────
earliest_ts = last_run[0][0]
latest_ts   = last_run[-1][0]
count       = len(last_run)

print(
    f"Last run detected: {count} move(s) between "
    f"{earliest_ts.strftime('%H:%M:%S')} and "
    f"{latest_ts.strftime('%H:%M:%S')} "
    f"on {earliest_ts.strftime('%Y-%m-%d')}"
)
print()

try:
    answer = input("Confirm undo? [y/n]: ").strip().lower()
except (EOFError, KeyboardInterrupt):
    print("\nCancelled.")
    sys.exit(0)

if answer not in ("y", "yes"):
    print("Cancelled.")
    sys.exit(0)

print()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 7 — Perform the undo moves, one by one.
#
# For each log entry:
#   new_path = where janitor.py PUT the file (its current location)
#   old_path = where janitor.py TOOK it FROM (where we want it back)
#
# We apply three safety checks before every move:
#   1. Is the file still at new_path?  (user may have moved or deleted it)
#   2. Is old_path already occupied?   (never overwrite anything)
#   3. Does old_path's parent folder exist?  (the source folder may be gone)
#
# We wrap shutil.move in try/except so unexpected OS errors (e.g. permissions)
# don't crash the whole undo run — we log the problem and move on.
# ─────────────────────────────────────────────────────────────────────────────
reversed_count    = 0
skipped_missing   = 0
skipped_collision = 0

for ts, old_path, new_path in last_run:

    # Safety check 1 — is the file still where the log says it is?
    if not new_path.exists():
        print(f"  WARNING: file not found at current location — skipping")
        print(f"           Expected: {new_path}")
        skipped_missing += 1
        continue

    # Safety check 2 — would we overwrite something at the original location?
    if old_path.exists():
        print(f"  WARNING: a file already exists at the original location — skipping")
        print(f"           Collision at: {old_path}")
        skipped_collision += 1
        continue

    # Safety check 3 — does the original folder still exist?
    # (The user may have deleted the Downloads folder root or a subfolder.)
    if not old_path.parent.exists():
        print(f"  WARNING: original folder no longer exists — skipping")
        print(f"           Missing: {old_path.parent}")
        skipped_missing += 1
        continue

    # All clear — perform the reverse move.
    try:
        shutil.move(str(new_path), str(old_path))
        print(f"  Undone: {new_path}  ->  {old_path}")
        reversed_count += 1

    except Exception as error:
        # Catch any OS-level error (permissions, locked file, disk full, …)
        # so one bad file doesn't stop the rest of the undo from completing.
        print(f"  ERROR: could not move '{new_path.name}': {error}")
        skipped_missing += 1


# ─────────────────────────────────────────────────────────────────────────────
# STEP 8 — Append the UNDO marker to the log.
#
# We write this marker AFTER all moves are done. Its timestamp acts as a
# natural boundary: the next time undo_last_run.py runs, it will stop here
# and not try to reverse moves that have already been undone.
#
# We use append mode ("a") so we never erase existing log content.
# ─────────────────────────────────────────────────────────────────────────────
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
marker_line = f"{timestamp} | --- UNDO RUN: reversed {reversed_count} moves ---\n"

with open(log_path, "a", encoding="utf-8") as f:
    f.write(marker_line)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 9 — Print the final summary.
# ─────────────────────────────────────────────────────────────────────────────
print()
print("--- Undo complete ---")
print(f"  Reversed:               {reversed_count}")
print(f"  Skipped (file missing): {skipped_missing}")
print(f"  Skipped (collision):    {skipped_collision}")
