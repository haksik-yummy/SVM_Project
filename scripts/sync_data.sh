#!/usr/bin/env bash
# 수집된 데이터(`data` 브랜치)를 data/collected/ 에 내려받거나 최신으로 갱신한다.
# 처음 실행하면 git worktree를 만들고, 이후에는 pull만 한다.
#
#   bash scripts/sync_data.sh

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

TARGET=data/collected

if ! git ls-remote --exit-code --heads origin data > /dev/null; then
  echo "원격에 아직 data 브랜치가 없습니다. 수집 워크플로가 한 번 이상 성공해야 생깁니다." >&2
  exit 1
fi

if [ -e "$TARGET/.git" ]; then
  git -C "$TARGET" pull --ff-only -q
else
  git fetch -q origin data
  if git show-ref --verify --quiet refs/heads/data; then
    git worktree add "$TARGET" data
    git -C "$TARGET" pull --ff-only -q
  else
    git worktree add --track -b data "$TARGET" origin/data
  fi
fi

echo "data/collected 갱신 완료:"
echo "  raw    파일 $(ls "$TARGET"/raw 2>/dev/null | wc -l)개, 최신 $(ls "$TARGET"/raw 2>/dev/null | tail -1)"
echo "  static 파일 $(ls "$TARGET"/static 2>/dev/null | wc -l)개"
