#!/bin/sh
# CONFIG_PULL [MSG="why"]: bring the printer config in line with GitHub main.
#   1. commit local edits  ("edit from printer: <MSG> [files]")
#   2. rebase them on origin/main and push
#   3. on a conflict: abort (nothing half-merged), push the local commits to a
#      new branch printer-edits/<timestamp>, reset the printer to origin/main,
#      and say so in the console. Claude merges the branch later.
cd "$HOME/printer_data/config" || exit 1
MSG="$1"
git add -A
files=$(git diff --cached --name-only | tr '\n' ' ')
if [ -n "$files" ]; then
    if [ -n "$MSG" ]; then m="edit from printer: $MSG [$files]"; else m="edit from printer: $files"; fi
    git commit -qm "$m" && echo "committed: $m"
fi
git fetch -q origin main || { echo "fetch failed"; exit 1; }
if git rebase -q origin/main; then
    echo "config at origin/main $(git rev-parse --short HEAD)"
    git push -q origin main 2>/dev/null && echo "local edits pushed to main"
    exit 0
fi
conflicted=$(git diff --name-only --diff-filter=U | tr '\n' ' ')
git rebase --abort
branch="printer-edits/$(date +%Y%m%d-%H%M)"
if git push -q origin "HEAD:$branch"; then
    echo "CONFLICT in: $conflicted"
    echo "Your edits are saved on GitHub branch $branch. Printer reset to origin/main. Ask Claude to merge $branch."
    git reset -q --hard origin/main
else
    echo "CONFLICT in: $conflicted - and pushing the backup branch failed. Nothing changed on the printer; check network and run CONFIG_PULL again."
fi
exit 0
