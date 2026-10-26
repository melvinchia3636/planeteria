#!/usr/bin/env bash
# Publish the contents of web/ to the gh-pages branch.
#
# The generated globe data (web/<body>/*.js) is gitignored to keep main small,
# so the site is built on a separate branch. GitHub Pages serves that branch at
# https://<owner>.github.io/<repo>/.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
branch="gh-pages"
base="$(mktemp -d)"
wt="$base/wt"

cleanup() {
    git -C "$root" worktree remove --force "$wt" >/dev/null 2>&1 || true
    rm -rf "$base"
}
trap cleanup EXIT

if git -C "$root" show-ref --verify --quiet "refs/heads/$branch"; then
    # Rebuild on top of the existing branch (same content = no-op commit).
    git -C "$root" worktree add --detach "$wt" "$branch" >/dev/null
else
    git -C "$root" worktree add --detach "$wt" >/dev/null
    git -C "$wt" checkout --orphan "$branch" >/dev/null 2>&1
fi
git -C "$wt" rm -rf . >/dev/null 2>&1 || true

# Copy the built site (index.html, d3, per-body data) to the branch root.
( cd "$root/web" && tar cf - --exclude='.DS_Store' . ) | ( cd "$wt" && tar xf - )
touch "$wt/.nojekyll"   # serve files as-is, no Jekyll processing

git -C "$wt" add -A
if git -C "$wt" diff --cached --quiet; then
    echo "gh-pages already up to date"
else
    git -C "$wt" commit -q -m "deploy: publish web portal"
fi
git -C "$wt" push -f origin "HEAD:refs/heads/$branch"
git -C "$root" branch -f "$branch" "$(git -C "$wt" rev-parse HEAD)" 2>/dev/null || true
