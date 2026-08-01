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

if [[ "$OSTYPE" == "darwin"* ]]; then
  OLD_JSON="$(mktemp -t bedrock_models_old)"
else
  OLD_JSON="$(mktemp -t bedrock_models_old.XXXX --suffix=.json)"
fi

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
Read the commit list and the diff of the generated model-ID class below, then produce a concise, human-readable TL;DR and structured changelog aimed at library users.

CRITICAL RULES:
1. DO NOT include markdown code fences (e.g. \`\`\`markdown or \`\`\`) surrounding the entire response.
2. DO NOT include any preamble or introductory text (e.g. \"Here are the release notes:\").
3. DO NOT include any postamble or signature block.
4. Output raw markdown immediately starting with the Headline block.

EXACT OUTPUT FORMAT:
[One-sentence headline summarizing the main focus of this release, e.g. \"Adds support for Amazon Nova 2 models and updates region metadata.\"]

## TL;DR
- [3 to 6 bullet points detailing the most impactful changes, focusing on newly added, removed, or deprecated Bedrock models, or new library features.]

[Include the following sections ONLY if they contain one or more items. Do not output empty headers or placeholders:]
### Added
- [Bullet points of added models, regions, or features]

### Changed
- [Bullet points of modified metadata, updates, or deprecated models]

### Removed
- [Bullet points of removed/deleted models]

### Fixed
- [Bullet points of metadata corrections or bug fixes]

--- CONTEXT ---
$(cat "$CONTEXT_FILE")"

# Headless / non-interactive kiro-cli run.
# Confirm exact flags for your installed version with: kiro-cli chat --help
# Pipe to sed to strip ANSI escape codes so that they do not get uploaded to GitHub Releases.
kiro-cli chat --no-interactive --trust-all-tools "$PROMPT" | sed 's/\x1b\[[0-9;]*[a-zA-Z]//g'
