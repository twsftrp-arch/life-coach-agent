#!/bin/bash
set -e

# 스크립트가 종료(성공이든 실패든)될 때 항상 원래 계정으로 복구하도록 trap 설정
cleanup() {
    echo "Switching gh auth back to trinity-mathslab..."
    gh auth switch -u trinity-mathslab
}
trap cleanup EXIT

echo "Switching gh auth to twsftrp-arch..."
gh auth switch -u twsftrp-arch

# working tree dirty 에러 해결을 위해 모든 변경사항 추가
git add .
# docs/SESSION-HANDOFF.md가 .gitignore에 있으므로 강제 추가하여 커밋 (git guard 통과용)
git add -f docs/SESSION-HANDOFF.md

git commit -m "feat: Add Trinity RAG Assistant LangGraph notebook, update requirements and push script"

echo "Pushing to main..."
git push origin main

echo "Done! 🎉"
