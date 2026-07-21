#!/usr/bin/env bash
#
# Generate a human-readable TL;DR release summary using kiro-cli (headless).
#
# The diff sent to the model is intentionally scoped to the generated model
# class file, since that is where model additions/removals/deprecations land
# and is the most relevant signal for users of this package.
#
# Requires:
#   - kiro-cli on PATH, authenticated (see release.yml auth step).
#   - Run from the repo root with full git history/tags available.
#
set -euo pipefail

MODEL_CLASS_FILE="packages/shared/bedrock_models.json"

# Determine the previous tag to diff against.
PREV_TAG="$(git describe --tags --abbrev=0 "HEAD^" 2>/dev/null || true)"
if [ -n "$PREV_TAG" ]; then
  RANGE="$PREV_TAG..HEAD"
else
  # No prior tag: diff from the first commit.
  RANGE="$(git rev-list --max-parents=0 HEAD | tail -n1)..HEAD"
fi

# Build context: commit subjects for the whole release + structured model diff.
CONTEXT_FILE="$(mktemp)"
OLD_JSON="$(mktemp -t bedrock_models_old.XXXX --suffix json"
trap 'rm -f "$CONTEXT_FILE" "$OLD_JSON"' EXIT

# Extract the version of the model file at the start of the range.
RANGE_START="${RANGE%..*}"
git show "${RANGE_START}:${MODEL_CLASS_FILE}" > "$OLD_JSON"

{
  echo "## Commits in $RANGE"
  git log --pretty=format:"- %s (%an)" "$RANGE"
  echo
  echo
  echo "## Model changes ($MODEL_CLASS_FILE)"
  python3 scripts/diff_models.py "$OLD_JSON" "$MODEL_CLASS_FILE"
} > "$CONTEXT_FILE"

PROMPT="You are writing GitHub release notes for the 'bedrock-models' project.
Read the commit list and the diff of the generated model-ID class below, then
produce a concise, human-readable TL;DR aimed at library users.

Format (markdown, no surrounding code fences, no preamble):
- One-sentence headline of the release.
- A '## TL;DR' section with 3-6 bullets covering the most impactful changes,
  especially newly added, removed, or deprecated Bedrock models.
- Optionally group notable items under 'Added', 'Changed', 'Fixed' if relevant.

--- CONTEXT ---
$(cat "$CONTEXT_FILE")"

# Headless / non-interactive kiro-cli run.
# Confirm exact flags for your installed version with: kiro-cli chat --help
kiro-cli chat --no-interactive --trust-all-tools "$PROMPT"
