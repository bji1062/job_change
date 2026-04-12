#!/usr/bin/env bash
#
# scripts/install-git-hooks.sh — 저장소에 등록된 git 훅을 .git/hooks 에 설치
#
# 사용법 (저장소 루트에서):
#   ./scripts/install-git-hooks.sh
#
# 이후 브랜치를 전환할 때마다 post-checkout 훅이 자동으로
# server/.env 심볼릭 링크를 브랜치별 환경 파일로 교체합니다.

set -e

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

src_dir="scripts/hooks"
dst_dir=".git/hooks"

if [ ! -d "$src_dir" ]; then
  echo "[install-git-hooks] $src_dir 디렉터리가 없습니다." >&2
  exit 1
fi
if [ ! -d "$dst_dir" ]; then
  echo "[install-git-hooks] $dst_dir 디렉터리가 없습니다. (git 저장소인지 확인)" >&2
  exit 1
fi

installed=0
for src in "$src_dir"/*; do
  [ -f "$src" ] || continue
  name="$(basename "$src")"
  dst="$dst_dir/$name"
  cp "$src" "$dst"
  chmod +x "$dst"
  echo "  installed: $dst"
  installed=$((installed + 1))
done

echo ""
echo "[install-git-hooks] $installed 개 훅 설치 완료."
echo ""
echo "다음 단계:"
echo "  1) cp server/.env.oracle.example  server/.env.oracle"
echo "  2) cp server/.env.refactor.example server/.env.refactor"
echo "  3) 두 파일의 DB_PASS / JWT_SECRET 값을 수정"
echo "  4) git checkout claude/oracle-server-setup-c1LNU    # 또는 refactor 브랜치"
echo "     → post-checkout 훅이 자동으로 server/.env 를 교체합니다."
