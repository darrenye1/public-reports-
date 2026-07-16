#!/bin/bash
# Run from Git Bash: Repository → Open in Git Bash → bash resolve_merge.sh
# Resolves PDF/JS merge conflicts by keeping YOUR branch, then lists any code files left.

set -e
cd "$(dirname "$0")"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Not a git repo."
  exit 1
fi

if ! git diff --name-only --diff-filter=U | grep -q .; then
  echo "No merge conflicts right now."
  echo "If you need to finish a merge, run: git merge <branch> first."
  exit 0
fi

echo "=== Step 1: Keep YOUR branch for all PDF + generated JS ==="

git checkout --ours -- \
  reports/ \
  public/reports/ \
  docs/reports/ \
  public/summary-data.js \
  public/dashboard-data.js \
  docs/summary-data.js \
  docs/dashboard-data.js \
  2>/dev/null || true

git add -- \
  reports/ \
  public/reports/ \
  docs/reports/ \
  public/summary-data.js \
  public/dashboard-data.js \
  docs/summary-data.js \
  docs/dashboard-data.js \
  2>/dev/null || true

echo ""
echo "=== Step 2: Remaining conflicts (must fix manually) ==="
REMAINING=$(git diff --name-only --diff-filter=U || true)
if [ -z "$REMAINING" ]; then
  echo "(none — all clear)"
else
  echo "$REMAINING"
  echo ""
  echo "Open the files above in VS Code/Cursor, remove <<<<<<< markers, save, then:"
  echo "  git add <each-file>"
fi

echo ""
echo "=== Step 3: When no conflicts left ==="
echo "  git commit -m \"Merge remote tracking branch\""
echo "  python equity_research.py --batch-top20 --force"
echo "  python sync_website.py"
echo ""
echo "=== Step 4: Stop future PDF conflicts (run once after merge) ==="
echo "  git rm -r --cached reports/*_research.pdf reports/Top20_Summary.pdf public/reports docs/reports 2>/dev/null || true"
echo "  git add .gitignore"
echo "  git commit -m \"Stop tracking generated PDFs\""
