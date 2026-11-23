#!/usr/bin/env bash
# Creates all 41 QANUN-VAR issues with bodies + labels + milestones.
# Requires: gh auth login; run from repo root. Repo owner auto-detected.
set -euo pipefail
REPO="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"
CSV="qanun-var-issues.csv"

# Milestones: create once if missing
declare -A MILE=( [G1-Day2]="Gate 1 - Day 2: KB & Skeleton" [G2-Day4]="Gate 2 - Day 4: F1 End-to-End"
                  [G3-Day7]="Gate 3 - Day 7: All Features" [G4-Day9]="Gate 4 - Day 9: Evaluation"
                  [G5-Day10]="Gate 5 - Day 10: Delivery" )
for key in "${!MILE[@]}"; do
  if ! gh api repos/"$REPO"/milestones --jq '.[].title' | grep -qx "${MILE[$key]}"; then
    gh api repos/"$REPO"/milestones --method POST -f title="${MILE[$key]}" -f state=open >/dev/null
  fi
done

# Resolve assignee emails -> GitHub usernames (cache in a file)
declare -A USER
[ -f .assignee-cache ] && source .assignee-cache
resolve() {  # $1 = email
  local email="$1"
  if [ -z "$email" ]; then echo ""; return; fi
  if [ -z "${USER[$email]:-}" ]; then
    local u
    u=$(gh api "search/users?q=$email+in:email" --jq '.items[0].login // empty' 2>/dev/null || true)
    USER[$email]="$u"
    echo "USER[$email]='$u'" >> .assignee-cache
  fi
  echo "${USER[$email]}"
}

tail -n +2 "$CSV" | while IFS=, read -r title body assignee labels milestone _; do
  args=(--title "$title" --body "$body" --label "$labels")
  [ -n "$milestone" ] && args+=(--milestone "${MILE[$milestone]}")
  a=$(resolve "$assignee")
  [ -n "$a" ] && args+=(--assignee "$a")
  gh issue create --repo "$REPO" "${args[@]}" || echo "FAILED: $title (check labels exist: task,critical-path,kb-f1,f2-docs,f3-eval,f4-frontend,lead)"
done
echo "Done. Labels not found will fail a row - create them in the UI first or rerun."
