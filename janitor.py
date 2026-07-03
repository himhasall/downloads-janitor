# janitor.py
# Downloads Folder Janitor — Sessions 3 & 4: Move Files (Interactive + Auto)
#
# Two modes of operation:
#
#   python3 janitor.py          — INTERACTIVE mode (default)
#       Asks y/n/q before every file. You stay in full control.
#       Use this when you want to review each file before moving it.
#
#   python3 janitor.py --auto   — AUTO mode
#       Moves every categorised file immediately, no prompts.
#       Use this when you trust the classification rules and want
#       a hands-free clean-up — e.g. on a schedule or in a script.
#
# In BOTH modes:
#   • Collision-safe renaming (" (1)", " (2)" …) — never overwrites
#   • Every move is logged to janitor_log.txt in the same format
#   • One failed move never kills the rest of the run
#
# New concept introduced this session:
#   • argparse — the standard-library module for parsing command-line flags.
#     It automatically generates --help text and gives clean error messages
#     for unknown flags, so you don't have to parse sys.argv manually.

import sys
import json
import argparse
import shutil
from pathlib import Path
from datetime import datetime


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Load settings from config.json.
#
# Beginners: all the customisable bits — which file extensions go in which
# category, where your Downloads folder lives, and whether empty category
# folders should be skipped — live in config.json, NOT in this script. Open
# config.json in any text editor to add extensions or whole new categories
# without touching a single line of Python.
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

# Convert the lists of extensions from config.json into sets (same shape the
# rest of the script expects — fast membership testing, no duplicates).
EXTENSION_MAP = {name: set(exts) for name, exts in config["categories"].items()}

# A set of all destination folder names — used to skip them while iterating.
DESTINATION_FOLDERS = set(EXTENSION_MAP.keys())


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — Key paths: Downloads folder and the log file location.
#
# The log lives in the WORKSPACE folder (same directory as this script),
# NOT inside Downloads. That way it survives even if Downloads is reorganised.
#
# The Downloads location comes from config.json ("downloads_path"). We call
# .expanduser() so a leading "~" is expanded to your home folder correctly.
# Path(__file__).parent gives us the directory that contains janitor.py —
# a reliable way to find the workspace without hardcoding any path.
# ─────────────────────────────────────────────────────────────────────────────
downloads = Path(config["downloads_path"]).expanduser()
log_path  = Path(__file__).parent / "janitor_log.txt"

# Guard clause: stop cleanly if Downloads doesn't exist.
if not downloads.exists():
    print(f"Error: Downloads folder not found at '{downloads}'")
    print("Please check that the path exists and try again.")
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2b — Parse command-line arguments with argparse.
#
# ArgumentParser builds a mini command-line interface for us. We register
# every flag we want to support, and argparse handles parsing, validation,
# and --help text generation automatically.
#
# add_argument("--auto", action="store_true") means:
#   • If the user passes --auto, args.auto is True.
#   • If they don't pass it, args.auto is False.
#   • action="store_true" is the standard pattern for boolean on/off flags —
#     no value after the flag is needed, just its presence or absence.
# ─────────────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(
    description="Downloads Folder Janitor — sorts files into category subfolders."
)
parser.add_argument(
    "--auto",
    action="store_true",
    help=(
        "Run without confirmation prompts. Every file that matches a category "
        "is moved immediately. Use when you trust the rules and want a "
        "hands-free clean-up. Without this flag the script asks y/n/q per file."
    ),
)
args = parser.parse_args()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Helper: classify a file by its extension.
#
# Returns the destination folder name (e.g. "Photos") or "SKIP" if no
# category matches. Lowercasing the extension makes the match case-insensitive,
# so ".JPG", ".Jpg", and ".jpg" all land in Photos.
# ─────────────────────────────────────────────────────────────────────────────
def classify(file_path):
    """Return the destination folder name for a file, or 'SKIP'."""
    ext = file_path.suffix.lower()
    for folder_name, extensions in EXTENSION_MAP.items():
        if ext in extensions:
            return folder_name
    return "SKIP"


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — Helper: resolve filename collisions without overwriting anything.
#
# If a file called "photo.jpg" already exists in the destination, we try
# "photo (1).jpg", then "photo (2).jpg", and so on until we find a name
# that isn't taken. We return the safe destination Path to use for the move.
#
# Path.stem  → filename without extension  (e.g. "photo")
# Path.suffix → extension with dot         (e.g. ".jpg")
# ─────────────────────────────────────────────────────────────────────────────
def safe_destination(destination_folder, filename):
    """
    Return a Path in destination_folder for filename that does not
    already exist. Appends ' (1)', ' (2)', ... before the extension
    if a collision is detected.
    Returns (path, was_renamed) where was_renamed is True if the name changed.
    """
    candidate = destination_folder / filename
    if not candidate.exists():
        return candidate, False   # no collision — use the name as-is

    stem      = Path(filename).stem    # "photo"
    extension = Path(filename).suffix  # ".jpg"
    counter   = 1
    while True:
        new_name  = f"{stem} ({counter}){extension}"   # "photo (1).jpg"
        candidate = destination_folder / new_name
        if not candidate.exists():
            return candidate, True    # found a free name
        counter += 1


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — Helper: append one line to the log file.
#
# open(path, "a") opens the file in APPEND mode — it adds to the end without
# erasing what's already there. If the file doesn't exist yet, Python creates
# it automatically. The "with" statement ensures the file is always closed
# properly, even if something goes wrong mid-write.
#
# We record the timestamp so a future "undo" script can sort moves by time.
# ─────────────────────────────────────────────────────────────────────────────
def log_move(old_path, new_path):
    """Append a timestamped move record to janitor_log.txt."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line      = f"{timestamp} | {old_path} -> {new_path}\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line)


def log_error(old_path, error_message):
    """Append a timestamped error record to janitor_log.txt."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line      = f"{timestamp} | ERROR moving {old_path}: {error_message}\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — Create destination subfolders (behaviour depends on config).
#
# config["skip_empty_folders"] decides HOW we create folders:
#
#   • True  → don't create anything up front. A category folder is only made
#             the moment the FIRST file needs to move into it (see STEP 8b).
#             This keeps Downloads tidy: no empty "Fonts/" folder appears just
#             because Fonts is a defined category you happen to have no fonts for.
#
#   • False → create every category folder now, up front (the original
#             behaviour). You'll always see all 13 folders, even empty ones.
#
# mkdir(exist_ok=True) creates the folder if missing and stays silent if it
# already exists — so this block is always safe to run.
# ─────────────────────────────────────────────────────────────────────────────
skip_empty_folders = config["skip_empty_folders"]

if not skip_empty_folders:
    print("Checking / creating destination folders...")
    for folder_name in EXTENSION_MAP:
        folder_path = downloads / folder_name
        folder_path.mkdir(exist_ok=True)
        print(f"  {'[ok]':5}  {folder_path}")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 7 — Counters for the final summary.
#
# We track four numbers:
#   moved          — files confirmed and moved successfully
#   skipped_user   — files the user said "n" to (interactive mode only)
#   skipped_auto   — files with no matching category (SKIP)
#   renamed        — files renamed due to a collision in the target
# ─────────────────────────────────────────────────────────────────────────────
moved        = 0
skipped_user = 0
skipped_auto = 0
renamed      = 0


# ─────────────────────────────────────────────────────────────────────────────
# STEP 8 — Main loop: iterate, classify, confirm (if interactive), move.
#
# We sort() the items so files appear in alphabetical order — makes it
# easier to track where you are in the list.
# ─────────────────────────────────────────────────────────────────────────────
for item in sorted(downloads.iterdir()):

    # ── Filter 1: skip hidden files (e.g. .DS_Store) ─────────────────────────
    if item.name.startswith("."):
        continue

    # ── Filter 2: skip directories (including our own destination folders) ────
    if item.is_dir():
        continue

    # ── Filter 3: classify the file ──────────────────────────────────────────
    category = classify(item)

    if category == "SKIP":
        skipped_auto += 1
        continue   # silently pass over files with no matching extension

    destination_folder = downloads / category

    # ── STEP 8a — Decide: auto mode or interactive mode? ─────────────────────
    # args.auto is True when the user passed --auto on the command line.
    # In auto mode we skip the prompt entirely and go straight to the move.
    # In interactive mode we ask y/n/q exactly as before — nothing changes.
    if not args.auto:
        # ── INTERACTIVE: ask the user what to do ─────────────────────────────
        # input() prints the prompt string and waits for the user to press Enter.
        # .strip() removes accidental leading/trailing spaces from the answer.
        # .lower() means "Y", "YES", "Yes" all work the same as "y".
        prompt = f"Move: {item.name}  ->  {category}/   [y/n/q]: "

        try:
            answer = input(prompt).strip().lower()
        except (EOFError, KeyboardInterrupt):
            # EOFError happens if stdin closes (e.g. piped input ends).
            # KeyboardInterrupt happens if the user presses Ctrl-C.
            # In both cases, treat it like a quit command.
            print("\nInterrupted — stopping.")
            break

        if answer in ("q", "quit"):
            # Quit: stop the whole script immediately.
            print("Quitting.")
            break

        if answer in ("n", "no"):
            # Skip: leave this file alone, move on to the next.
            skipped_user += 1
            continue

        # Anything else (including just pressing Enter) is treated as "yes".
        # This means the user can fly through confirmations quickly.

    # ── STEP 8b — Resolve collisions and move the file ───────────────────────
    # This block runs in BOTH modes. safe_destination() returns the Path to
    # use and tells us if a rename happened. We wrap shutil.move() in
    # try/except so a permission error or locked file doesn't crash the script.
    #
    # When skip_empty_folders is True we didn't create folders up front, so we
    # create this category's folder on demand right before the first move into
    # it. mkdir(exist_ok=True) is a no-op once the folder already exists.
    if skip_empty_folders:
        destination_folder.mkdir(exist_ok=True)

    dest_path, was_renamed = safe_destination(destination_folder, item.name)

    try:
        shutil.move(str(item), str(dest_path))

        # Record the move in the log file — same format in both modes.
        log_move(item, dest_path)
        moved += 1

        if was_renamed:
            renamed += 1
            if args.auto:
                print(f"  Moved: {item.name} -> {category}/ (renamed: {dest_path.name})")
            else:
                print(f"  Moved as: {dest_path.name}  (renamed — collision avoided)")
        else:
            if args.auto:
                print(f"  Moved: {item.name} -> {category}/")
            else:
                print(f"  Moved.")

    except Exception as error:
        # Exception is the base class for all Python errors, so this catches
        # anything that can go wrong: permission denied, disk full, etc.
        # We print the error and log it, then continue with the next file.
        print(f"  ERROR: could not move '{item.name}': {error}")
        log_error(item, str(error))


# ─────────────────────────────────────────────────────────────────────────────
# STEP 9 — Print the final summary.
#
# We show a different summary block depending on the mode:
#   • Auto mode:        concise, no mention of "skipped by user" (irrelevant)
#   • Interactive mode: unchanged from Session 3 — same wording as before
#
# The log file (janitor_log.txt) contains the full auditable record in both.
# ─────────────────────────────────────────────────────────────────────────────
print()
if args.auto:
    print("--- Auto run complete ---")
    print(f"  Moved:                      {moved}")
    print(f"  Auto-skipped (no category): {skipped_auto}")
    print(f"  Renamed due to collision:   {renamed}")
    print(f"  Errors:                     0")
    print()
    print(f"  See janitor_log.txt for full details.")
else:
    print("--- Done ---")
    print(f"  Moved:                    {moved}")
    print(f"  Skipped by user:          {skipped_user}")
    print(f"  Auto-skipped (no category): {skipped_auto}")
    print(f"  Renamed due to collision: {renamed}")
    print()
    print(f"  Log written to: {log_path}")
