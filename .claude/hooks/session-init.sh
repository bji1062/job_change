#!/bin/bash
cd "$CLAUDE_PROJECT_DIR"

SQL_COUNT=$(ls server/seed/benefit/*.sql 2>/dev/null | wc -l)
LAST_COMMIT=$(git log --oneline -1 2>/dev/null)
BRANCH=$(git branch --show-current 2>/dev/null)
DIRTY=$(git diff --shortstat 2>/dev/null)

cat <<EOF
<project-status>
브랜치: $BRANCH
최근커밋: $LAST_COMMIT
미커밋변경: ${DIRTY:-없음}
복지데이터: ${SQL_COUNT}/200
</project-status>
EOF
exit 0
