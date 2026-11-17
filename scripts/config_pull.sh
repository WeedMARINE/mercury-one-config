#!/bin/sh
# CONFIG_PULL: bring the printer config in line with GitHub main.
# Local edits are committed first and rebased on top of the remote. On a
# conflict nothing is left half-merged: local commits go to branch
# "printer-edits" on GitHub, the printer is reset to origin/main, and the
# console says what happened.
cd "$HOME/printer_data/config" || exit 1
git add -A
git commit -qm "edit from printer" 2>/dev/null && echo "committed local edits"
git fetch -q origin main || { echo "fetch failed"; exit 1; }
if git rebase -q origin/main; then
    echo "config up to date with origin/main ($(git rev-parse --short HEAD))"
    git push -q origin main 2>/dev/null && echo "local edits pushed"
    exit 0
fi
files=$(git diff --name-only --diff-filter=U | tr '\n' ' ')
git rebase --abort
git push -qf origin HEAD:printer-edits && echo "CONFLICT in: $files"
echo "Your edits are saved on GitHub branch printer-edits; printer reset to origin/main. Ask Claude to merge."
git reset -q --hard origin/main
exit 0
