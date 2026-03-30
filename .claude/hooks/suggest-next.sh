#!/bin/bash
INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
[ -z "$FILE" ] && exit 0

case "$FILE" in
  */index.html)
    echo "<next-step>FE 변경 → '/test' 실행 권장</next-step>" ;;
  */server/routers/*|*/server/models/*|*/server/services/*)
    echo "<next-step>BE 변경 → '/test' 실행 권장</next-step>" ;;
  */server/seed/schema.sql)
    echo "<next-step>스키마 변경 → models/routers 동기화 필요</next-step>" ;;
  */server/seed/benefit/*)
    echo "<next-step>복지 데이터 변경 → '/batch-benefits'로 진행률 확인</next-step>" ;;
  */infra/*|*/server/deploy/*)
    echo "<next-step>인프라 변경 → '/deploy'로 상태 확인</next-step>" ;;
esac
exit 0
