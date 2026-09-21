#!/usr/bin/env bash
set -euo pipefail
TARGET="claude"; DEST=""; REF="main"; REPO="WaytoAIC/waytoaic-voc-insight"; NAME="voc-insight"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) TARGET="$2"; shift 2;;
    --dest) DEST="$2"; shift 2;;
    --ref) REF="$2"; shift 2;;
    --repo) REPO="$2"; shift 2;;
    -h|--help) echo "usage: install.sh [--target claude|codex|openclaw] [--dest DIR] [--ref REF] [--repo OWNER/NAME]"; exit 0;;
    *) echo "unknown arg: $1" >&2; exit 1;;
  esac
done
if [[ -z "$DEST" ]]; then
  case "$TARGET" in
    claude) DEST="$HOME/.claude/skills";;
    codex) DEST="$HOME/.codex/skills";;
    openclaw) DEST="$HOME/.openclaw/skills";;
    *) echo "unknown target: $TARGET (claude|codex|openclaw)" >&2; exit 1;;
  esac
fi
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
git clone --depth 1 --branch "$REF" "https://github.com/$REPO.git" "$TMP/repo" >/dev/null 2>&1
mkdir -p "$DEST/$NAME"
rm -rf "$DEST/$NAME/references" "$DEST/$NAME/scripts" "$DEST/$NAME/assets"
cp -r "$TMP/repo/skill/." "$DEST/$NAME/"
echo "Installed to $DEST/$NAME"
echo "Next: pip install -r $DEST/$NAME/requirements.txt"
echo "Restart your agent, then say: 分析一下这款的退货 / 看看评论里客户在说什么"
