# Storybook Workflow Agent

Google ADK Workflow Agent로 만든 어린이 동화책 파이프라인입니다.

## Pipeline

1. `SequentialAgent`가 전체 흐름을 고정 순서로 실행합니다.
2. `StoryWriterAgent`가 사용자 테마를 받아 5페이지 동화 JSON을 작성하고 Agent State의 `storybook_story_json`에 저장합니다.
3. `ParallelIllustratorAgent`가 5개의 `IllustratorPage*Agent`를 동시에 실행합니다.
4. 각 Illustrator Agent는 페이지별 SVG 삽화를 만들고 ADK Artifact로 저장합니다.
5. `StorybookAssemblerAgent`가 제목, 5페이지 텍스트, 5개 이미지 Artifact를 최종 동화책으로 조립합니다.

Callbacks는 각 단계의 진행 상황을 Agent State의 `storybook_progress:*` 키에 기록합니다.

## Run

```bash
STORYBOOK_ADK_USE_LLM=0 \
uv run --python 3.12 --with-requirements requirements.txt adk web storybook_workflow
```

ADK Web UI에서 예시 프롬프트:

```text
용감한 아기 고양이 이야기
```

```text
달빛 도서관을 여행하는 작은 토끼 이야기
```

## Environment

모델 키 값은 커밋하지 않습니다. 환경 변수 이름만 사용합니다.

- `STORYBOOK_ADK_USE_LLM=0`: 모델 키 없이 로컬 fallback Story Writer 사용
- `STORYBOOK_ADK_USE_LLM=1`: LLM Story Writer 강제 사용
- `GOOGLE_API_KEY`: Gemini 모델 사용
- `GOOGLE_ADK_MODEL`: 기본값 `gemini-2.5-flash`
- `DEEPSEEK_API_KEY`: `STORYBOOK_ADK_USE_DEEPSEEK=1` 또는 `STORYBOOK_ADK_MODEL` 지정 시 LiteLLM을 통해 사용
- `STORYBOOK_ADK_USE_DEEPSEEK=1`: DeepSeek/OpenAI-compatible Writer 사용
- `STORYBOOK_ADK_MODEL`: 예 `openai/deepseek-v4-flash`
- `STORYBOOK_ADK_API_BASE`: 기본값 `https://api.deepseek.com`

## Recording Checklist

2-3분 화면 녹화에서는 다음 순서로 보여주면 됩니다.

1. `adk web storybook_workflow` 실행 후 Web UI 열기
2. Demo 1 프롬프트 입력
3. `StoryWriterAgent`, `ParallelIllustratorAgent`, `IllustratorPage1Agent`-`IllustratorPage5Agent` 실행 흐름 확인
4. 최종 동화책 출력과 5개 Artifact 확인
5. 새 세션 또는 새 입력으로 Demo 2 프롬프트 입력
6. 다른 테마의 제목/페이지/Artifact가 생성되는지 확인
