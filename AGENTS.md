# AGENTS.md

이 폴더는 Nomad Coders 퀴즈(OpenAI Agents SDK + Streamlit) **복습 정리본** 작업 공간이다.

<!-- LOCAL_AGENT_SECRETS_START -->
## Local Agent Secrets

Supabase PAT bundle values must never be stored in this repo. For an explicit Supabase account/project audit task, resolve the PAT bundle in this order:

1. `$SUPABASE_AUDIT_PAT_FILE`
2. `$HOME/Private/agent-keys/supabase-audit.env`
3. Legacy fallback: `$HOME/Library/CloudStorage/GoogleDrive-gptalt1729@gmail.com/My Drive/Document/supabase-audit.txt`

Rules:
- Never print PAT, token, API key, auth header, or full connection-string values.
- Only print account labels and `configured` / `missing` / `confirmed` status.
- Do not copy secrets into repo files, logs, docs, screenshots, prompts, or chat.
- Use these PATs only for the explicit Supabase task requested by the user.
- Prefer read-only inspection. Ask before destructive actions, billing changes, project transfer, pause/resume, deletion, or secret rotation.
<!-- LOCAL_AGENT_SECRETS_END -->

## 먼저 읽을 것
- **`SESSION-HANDOFF.md`** — 이전 세션(Claude)의 작업 상태·산출물·PDF 재현 방법·다음 단계.
  작업을 시작하기 전에 반드시 먼저 읽을 것.

## 핵심 산출물
- `/Users/sungminkim/Desktop/OpenAI-Agents-SDK_퀴즈정리.md` — 정리본 원본(MD)
- `/Users/sungminkim/Desktop/OpenAI-Agents-SDK_퀴즈정리.pdf` — 배포용 PDF (5p)
- `quiz.html` (이 폴더) — PDF 생성 소스. **MD를 고치면 이 HTML도 같이 고치고 PDF 재생성**.

## 운용 규칙 (성민님)
- 한국어로 답하고, 호칭은 "성민님".
- commit/push/branch, 스키마·인증·결제·공개 API·의존성·배포 설정 변경은 **명시 승인 전까지 금지**
  (이 폴더는 git 레포도 아님 — 커밋 대상 없음).
- 의미 있는 상태 변화마다 `SESSION-HANDOFF.md`를 갱신.
- 미완성 상태로 성민님에게 선택을 묻지 말고, 구현·검증을 마친 뒤 증거와 함께 보고.
