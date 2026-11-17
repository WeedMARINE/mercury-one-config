#!/bin/sh
# CONFIG_PUSH [MSG="why"]: commit local edits and push to GitHub main (no pull).
cd "$HOME/printer_data/config" || exit 1
MSG="$1"
git add -A
files=$(git diff --cached --name-only | tr '\n' ' ')
if [ -z "$files" ]; then echo "nothing to commit"; else
    if [ -n "$MSG" ]; then m="edit from printer: $MSG [$files]"; else m="edit from printer: $files"; fi
    git commit -qm "$m" && echo "committed: $m"
fi
git push -q origin main 2>&1 && echo "pushed" || echo "push failed - run CONFIG_PULL to rebase first"
