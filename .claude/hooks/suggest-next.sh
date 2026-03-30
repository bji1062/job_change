#!/bin/bash
INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
[ -z "$FILE" ] && exit 0

case "$FILE" in
  */index.html)
    echo "<next-step>FE 변경 → 테스트 실행을 권장합니다.</next-step>" ;;
  */server/routers/*|*/server/models/*|*/server/services/*)
    echo "<next-step>BE 변경 → 테스트 실행을 권장합니다.</next-step>" ;;
  */server/seed/schema.sql)
    echo "<next-step>스키마 변경 → models/routers 동기화가 필요합니다.</next-step>" ;;
  */server/seed/benefit/*)
    echo "<next-step>복지 데이터 변경 → '/batch-benefits'로 진행률 확인하세요.</next-step>" ;;
  */infra/*|*/server/deploy/*)
    echo "<next-step>인프라 변경 → 배포 상태를 확인하세요.</next-step>" ;;
esac
exit 0
