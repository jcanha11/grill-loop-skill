#!/usr/bin/env bash
set -euo pipefail

REPO="jcanha11/grill-loop-skill"
REF="${GRILL_LOOP_REF:-main}"
SKILLS_DIR="${GRILL_LOOP_SKILLS_DIR:-${CODEX_SKILLS_DIR:-$HOME/.agents/skills}}"
TARGET="$SKILLS_DIR/grill-loop"

command -v curl >/dev/null 2>&1 || {
  echo "curl is required" >&2
  exit 1
}

command -v tar >/dev/null 2>&1 || {
  echo "tar is required" >&2
  exit 1
}

tmp="$(mktemp -d)"
cleanup() {
  rm -rf "$tmp"
}
trap cleanup EXIT

archive="$tmp/grill-loop.tar.gz"
url="https://github.com/$REPO/archive/refs/heads/$REF.tar.gz"

if [[ "$REF" == v* ]]; then
  url="https://github.com/$REPO/archive/refs/tags/$REF.tar.gz"
fi

echo "Downloading Grill Loop from $url"
curl -fsSL "$url" -o "$archive"
tar -xzf "$archive" -C "$tmp"

src=""
for candidate in "$tmp"/*/grill-loop; do
  if [[ -f "$candidate/SKILL.md" ]]; then
    src="$candidate"
    break
  fi
done

if [[ -z "$src" || ! -f "$src/SKILL.md" ]]; then
  echo "Could not find grill-loop/SKILL.md in downloaded archive" >&2
  exit 1
fi

mkdir -p "$SKILLS_DIR"

if [[ -e "$TARGET" ]]; then
  backup="$TARGET.backup.$(date +%Y%m%d%H%M%S)"
  echo "Existing install found. Moving it to $backup"
  mv "$TARGET" "$backup"
fi

cp -R "$src" "$TARGET"

echo "Installed Grill Loop to $TARGET"
echo "Start a new Codex session, then invoke it with: Use \$grill-loop in supervised mode to stress-test this plan."
