#!/usr/bin/env bash
# configure.sh — Replace placeholder values throughout the codebase
# Updated: 2026-03-29
#
# Usage:
#   1. Fill in config.env with your values
#   2. Run: bash configure.sh
#   3. Deploy the Cloud Function (see README)
#   4. Fill in CLOUD_FUNCTION_URL in config.env
#   5. Run: bash configure.sh   (again, to apply the Cloud Function URL)
#
# How it works:
#   Reads every KEY=VALUE pair from config.env. For each key with a non-empty
#   value, searches the codebase for that key as a literal string and replaces
#   it with the value. No hardcoded list — add a new key to config.env and a
#   matching placeholder in the code, and this script picks it up automatically.

set -euo pipefail

ENV_FILE="config.env"
EXCLUDE_FILES="REPO-CLEANUP-PLAN.md|README.md|configure.sh|config.env"

# --- Load config.env ---

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Error: $ENV_FILE not found."
  exit 1
fi

# --- Detect sed flavor (macOS vs Linux) ---

if sed --version 2>/dev/null | grep -q GNU; then
  SED_INPLACE=(sed -i)
else
  SED_INPLACE=(sed -i '')
fi

# --- Parse key-value pairs from config.env ---

declare -A CONFIG_PAIRS

while IFS= read -r line; do
  # Skip comments and blank lines
  [[ "$line" =~ ^[[:space:]]*# ]] && continue
  [[ -z "${line// }" ]] && continue

  # Split on first '='
  key="${line%%=*}"
  value="${line#*=}"

  # Trim whitespace
  key="$(echo "$key" | xargs)"
  value="$(echo "$value" | xargs)"

  CONFIG_PAIRS["$key"]="$value"
done < "$ENV_FILE"

# --- Display loaded values ---

echo "=== Configuration Values ==="
for key in "${!CONFIG_PAIRS[@]}"; do
  value="${CONFIG_PAIRS[$key]}"
  if [[ -z "$value" ]]; then
    echo "  $key: (not set)"
  else
    echo "  $key: $value"
  fi
done | sort
echo ""

# --- Perform replacements ---

do_replace() {
  local placeholder="$1"
  local value="$2"

  # Escape special characters for sed
  local escaped_value
  escaped_value=$(printf '%s\n' "$value" | sed 's/[&/\]/\\&/g')
  local escaped_placeholder
  escaped_placeholder=$(printf '%s\n' "$placeholder" | sed 's/[.[\*^$()+?{|\\]/\\&/g')

  local files
  files=$(grep -rl "$placeholder" --include="*.js" --include="*.html" --include="*.sh" --include="*.py" . 2>/dev/null \
    | grep -v node_modules | grep -v '.git/' | grep -Ev "$EXCLUDE_FILES" || true)

  if [[ -z "$files" ]]; then
    echo "  $placeholder — no occurrences found"
    return
  fi

  local count
  count=$(echo "$files" | wc -l | tr -d ' ')

  echo "$files" | while read -r file; do
    "${SED_INPLACE[@]}" "s|${escaped_placeholder}|${escaped_value}|g" "$file"
  done

  echo "  $placeholder -> $value  ($count file(s))"
}

echo "=== Applying replacements ==="

for key in $(echo "${!CONFIG_PAIRS[@]}" | tr ' ' '\n' | sort); do
  value="${CONFIG_PAIRS[$key]}"
  if [[ -n "$value" ]]; then
    do_replace "$key" "$value"
  fi
done

echo ""

# --- Verify ---

echo "=== Verification ==="
REMAINING=$(grep -rn "YOUR_" --include="*.js" --include="*.html" --include="*.sh" . 2>/dev/null \
  | grep -v node_modules | grep -v '.git/' | grep -Ev "$EXCLUDE_FILES" || true)

if [[ -z "$REMAINING" ]]; then
  echo "  All YOUR_* placeholders replaced. You're ready to deploy."
else
  echo "  Remaining YOUR_* placeholders (set these in config.env and re-run):"
  echo "$REMAINING" | while read -r line; do
    echo "    $line"
  done
fi

echo ""
echo "Next steps:"
if [[ -z "${CONFIG_PAIRS[CLOUD_FUNCTION_URL]:-}" ]]; then
  echo "  1. Deploy the Cloud Function:  cd cloud-functions/saver && npm install && bash deployment.sh"
  echo "  2. Copy the function URL into config.env as CLOUD_FUNCTION_URL"
  echo "  3. Run this script again:  bash configure.sh"
else
  echo "  1. Deploy the Cloud Function:  cd cloud-functions/saver && npm install && bash deployment.sh"
  echo "  2. Host the app (see README for GitHub Pages instructions)"
  echo "  3. Visit: ${CONFIG_PAIRS[GITHUB_PAGES_URL]:-YOUR_GITHUB_PAGES_URL}/pages/hosting/start_study.html"
fi
