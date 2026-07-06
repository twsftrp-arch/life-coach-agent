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

# 변경된 파일 모두 커밋 대상에 포함
git add qna_tutor_agent.ipynb push.sh requirements.txt
git commit -m "feat: Add Trinity RAG Assistant LangGraph notebook, update requirements and push script"

echo "Pushing to main..."
git push origin main

echo "Done! 🎉"
