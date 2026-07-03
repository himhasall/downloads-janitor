#!/bin/bash
# If double-clicking doesn't work, open Terminal, navigate to this folder, and run: chmod +x INSTALL.command

# Stop immediately if any command fails, so the script never does half a job.
set -e

echo "=== Downloads Janitor — Setup ==="
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — Make sure Python 3 is available.
# ─────────────────────────────────────────────────────────────────────────────
echo "Checking that Python 3 is installed..."
if ! python3 --version >/dev/null 2>&1; then
    echo ""
    echo "Python 3 is not installed on your Mac."
    echo "Please install it from https://www.python.org/downloads/ and re-run this installer."
    echo ""
    read -p "Press Enter to close..."
    exit 1
fi
echo "Found: $(python3 --version)"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Step 2 — Figure out which folder this installer lives in.
# This works no matter where the user unzipped the project (Desktop, Documents,
# Downloads — anywhere). Every file we look for is inside this same folder.
# ─────────────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Project folder: $SCRIPT_DIR"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Step 3 — Make sure the important files are all here.
# ─────────────────────────────────────────────────────────────────────────────
echo "Checking that all project files are present..."
missing=""
for needed in config.json janitor.py undo_last_run.py; do
    if [ ! -f "$SCRIPT_DIR/$needed" ]; then
        missing="$missing $needed"
    fi
done

if [ -n "$missing" ]; then
    echo ""
    echo "These files are missing:$missing"
    echo "Please make sure all project files are in the same folder as INSTALL.command."
    echo ""
    read -p "Press Enter to close..."
    exit 1
fi
echo "All files found."
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Step 4 — Prepare the category folders inside Downloads.
# If the project is set to create folders only when needed, we skip this and
# let the sorter make them on demand.
# ─────────────────────────────────────────────────────────────────────────────
echo "Setting up category folders in your Downloads folder..."
skip_empty="$(python3 -c "import json; print(json.load(open('$SCRIPT_DIR/config.json')).get('skip_empty_folders', False))")"

if [ "$skip_empty" = "True" ]; then
    echo "Folders will be created on demand when files are sorted."
else
    for category in $(python3 -c "import json; config=json.load(open('$SCRIPT_DIR/config.json')); [print(c) for c in config['categories']]"); do
        mkdir -p "$HOME/Downloads/$category"
        echo "Created folder: ~/Downloads/$category"
    done
fi
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Step 5 — Create two double-clickable shortcuts in the Downloads folder:
# one to sort, one to undo the last sort.
# ─────────────────────────────────────────────────────────────────────────────
echo "Creating your shortcuts..."

SORT_SHORTCUT="$HOME/Downloads-Janitor-Sort.command"
UNDO_SHORTCUT="$HOME/Downloads-Janitor-Undo.command"

cat > "$SORT_SHORTCUT" <<EOF
#!/bin/bash
cd "$SCRIPT_DIR"
python3 janitor.py --auto
echo ""
echo "Done! You can close this window."
read -p "Press Enter to close..."
EOF

cat > "$UNDO_SHORTCUT" <<EOF
#!/bin/bash
cd "$SCRIPT_DIR"
python3 undo_last_run.py --auto
echo ""
echo "Done! Undo complete. You can close this window."
read -p "Press Enter to close..."
EOF

chmod +x "$SORT_SHORTCUT"
chmod +x "$UNDO_SHORTCUT"

echo "Created shortcut: ~/Downloads-Janitor-Sort.command"
echo "Created shortcut: ~/Downloads-Janitor-Undo.command"
echo "You can double-click these anytime to sort or undo."
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Step 6 — Show the user what to do next.
# ─────────────────────────────────────────────────────────────────────────────
echo "=== Setup complete! ==="
echo ""
echo "To sort your Downloads folder:"
echo "Double-click ~/Downloads-Janitor-Sort.command"
echo ""
echo "To undo the last sort:"
echo "Double-click ~/Downloads-Janitor-Undo.command"
echo ""
echo "To customize categories:"
echo "Edit config.json in this folder with any text editor."
echo ""
echo "Questions or issues? Visit: https://github.com/himhasall/downloads-janitor"
echo ""
read -p "Press Enter to close..."
