from __future__ import annotations

import hashlib
import json
import os
import re
import time
from html import escape
from typing import Any, AsyncGenerator

from google.adk.agents import BaseAgent, LlmAgent, ParallelAgent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.models.llm_response import LlmResponse
from google.genai import types
from pydantic import Field

try:
    from google.adk.models.lite_llm import LiteLlm
except Exception:  # pragma: no cover - optional path when litellm is absent
    LiteLlm = None


TOTAL_PAGES = 5
STORY_STATE_KEY = "storybook_story_json"
FINAL_STATE_KEY = "storybook_final_markdown"
PROGRESS_PREFIX = "storybook_progress"
IMAGE_STATE_PREFIX = "storybook_image_"


def read_secret(name: str) -> str:
    value = os.getenv(name)
    if value:
        return value
    try:
        import streamlit as st

        secret_value = st.secrets.get(name)
    except Exception:
        secret_value = None
    return str(secret_value or "").strip()


def build_story_model() -> str | Any:
    configured_model = os.getenv("STORYBOOK_ADK_MODEL", "").strip()
    deepseek_key = read_secret("DEEPSEEK_API_KEY")

    if configured_model:
        if "/" not in configured_model:
            return configured_model
        if LiteLlm is None:
            return configured_model
        return LiteLlm(
            model=configured_model,
            api_key=deepseek_key or read_secret("OPENAI_API_KEY") or "unused",
            api_base=os.getenv("STORYBOOK_ADK_API_BASE", "https://api.deepseek.com"),
            drop_params=True,
        )

    use_deepseek = os.getenv("STORYBOOK_ADK_USE_DEEPSEEK", "").lower() in {
        "1",
        "true",
        "yes",
    }
    if use_deepseek and deepseek_key and LiteLlm is not None:
        return LiteLlm(
            model="openai/deepseek-v4-flash",
            api_key=deepseek_key,
            api_base=os.getenv("STORYBOOK_ADK_API_BASE", "https://api.deepseek.com"),
            drop_params=True,
        )

    return os.getenv("GOOGLE_ADK_MODEL", "gemini-2.5-flash")


def should_use_llm_writer() -> bool:
    setting = os.getenv("STORYBOOK_ADK_USE_LLM", "").lower()
    if setting in {"0", "false", "no"}:
        return False
    explicit = setting in {"1", "true", "yes"}
    return bool(explicit or read_secret("GOOGLE_API_KEY") or os.getenv("STORYBOOK_ADK_MODEL"))


def user_text_from_context(ctx: InvocationContext) -> str:
    if not ctx.user_content or not ctx.user_content.parts:
        return "용감한 아기 고양이 이야기"
    chunks = [part.text for part in ctx.user_content.parts if getattr(part, "text", None)]
    return " ".join(chunks).strip() or "용감한 아기 고양이 이야기"


def progress_callback(message: str):
    def _callback(callback_context: CallbackContext) -> None:
        key = f"{PROGRESS_PREFIX}:{callback_context.agent_name}"
        callback_context.state[key] = {
            "message": message,
            "seconds": round(time.perf_counter(), 3),
        }
        return None

    return _callback


def extract_json(raw_value: Any) -> dict[str, Any]:
    if isinstance(raw_value, dict):
        return raw_value
    text = str(raw_value or "").strip()
    if not text:
        raise ValueError("Story Writer Agent did not return JSON.")
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        for index, char in enumerate(text):
            if char not in "{[":
                continue
            try:
                payload, _ = decoder.raw_decode(text[index:])
                if isinstance(payload, dict):
                    return payload
            except json.JSONDecodeError:
                continue
    raise ValueError("Story Writer Agent output was not valid JSON.")


def fallback_story_from_theme(theme: str) -> dict[str, Any]:
    clean_theme = re.sub(r"\s+", " ", theme).strip() or "용감한 친구 이야기"
    subject = re.sub(r"(이야기|동화|스토리)$", "", clean_theme).strip() or clean_theme
    place = "작은 마을"
    travel_match = re.search(r"(.+?)(?:을|를)\s*여행하는\s+(.+)", subject)
    if travel_match:
        place = travel_match.group(1).strip()
        subject = travel_match.group(2).strip()
    if "도서관" in clean_theme:
        place = "달빛 도서관"
    elif "우주" in clean_theme:
        place = "반짝이는 우주 정거장"
    elif "바다" in clean_theme:
        place = "파도 소리가 들리는 바닷가"
    elif "숲" in clean_theme:
        place = "이슬 맺힌 숲속"

    if place and place not in subject:
        title = f"{subject}의 {place} 모험"
    else:
        title = subject if subject.endswith("모험") else f"{subject}의 작은 모험"
    return {
        "title": title[:80],
        "pages": [
            {
                "page": 1,
                "text": f"{place}에 {subject}가 살고 있었어요. 오늘 아침, 반짝이는 초대장이 창가에 내려앉았지요.",
                "visual": f"{place}에서 초대장을 발견한 {subject}, 따뜻한 아침빛과 설레는 표정",
            },
            {
                "page": 2,
                "text": f"{subject}는 두근거리는 마음으로 길을 나섰어요. 길 위의 작은 친구들이 손을 흔들며 응원했어요.",
                "visual": f"작은 길을 따라 걷는 {subject}, 주변 친구들의 응원과 부드러운 햇살",
            },
            {
                "page": 3,
                "text": "갑자기 커다란 그림자가 앞을 가렸지만, 주인공은 천천히 숨을 고르고 한 걸음 다가갔어요.",
                "visual": f"낯선 그림자 앞에서 용기를 내는 {subject}, 무섭지 않고 신비로운 분위기",
            },
            {
                "page": 4,
                "text": "그림자는 길을 잃은 작은 별빛이었어요. 주인공은 별빛이 집으로 돌아가도록 길을 밝혀 주었어요.",
                "visual": f"작은 별빛을 도와주는 {subject}, 주변에 반짝이는 빛과 따뜻한 미소",
            },
            {
                "page": 5,
                "text": f"밤이 되자 {place} 위로 별들이 환하게 웃었어요. {subject}는 오늘 배운 용기를 마음속에 꼭 안았답니다.",
                "visual": f"별빛 아래에서 환하게 웃는 {subject}, 평화로운 결말과 포근한 밤하늘",
            },
        ],
    }


def normalize_story(raw_value: Any, fallback_theme: str) -> dict[str, Any]:
    payload = extract_json(raw_value)
    title = str(payload.get("title") or f"{fallback_theme}").strip()[:80]
    raw_pages = payload.get("pages")
    if not isinstance(raw_pages, list) or len(raw_pages) < TOTAL_PAGES:
        raise ValueError("Story Writer Agent must return five pages.")

    pages: list[dict[str, Any]] = []
    for index, page in enumerate(raw_pages[:TOTAL_PAGES], start=1):
        if not isinstance(page, dict):
            raise ValueError(f"Page {index} is not an object.")
        text = re.sub(r"\s+", " ", str(page.get("text") or "")).strip()
        visual = re.sub(r"\s+", " ", str(page.get("visual") or text)).strip()
        if not text:
            raise ValueError(f"Page {index} has no text.")
        pages.append(
            {
                "page": index,
                "text": text[:320],
                "visual": visual[:360],
            }
        )
    return {"title": title, "pages": pages}


def story_writer_error_callback(
    callback_context: CallbackContext,
    _llm_request: Any,
    _exception: Exception,
) -> LlmResponse:
    theme = user_text_from_context(callback_context.get_invocation_context())
    story = fallback_story_from_theme(theme)
    callback_context.state[f"{PROGRESS_PREFIX}:StoryWriterAgentFallback"] = {
        "message": "모델 호출 실패로 로컬 Story Writer fallback 사용",
        "seconds": round(time.perf_counter(), 3),
    }
    return LlmResponse(
        content=types.Content(
            role="model",
            parts=[
                types.Part.from_text(
                    text=json.dumps(story, ensure_ascii=False),
                )
            ],
        )
    )


def artifact_slug(value: str) -> str:
    ascii_slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    if ascii_slug:
        return ascii_slug[:40]
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:10]
    return f"storybook-{digest}"


def wrap_text(text: str, max_chars: int, max_lines: int) -> list[str]:
    words = " ".join(text.split()).split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > max_chars:
            lines.append(current)
            current = word
        else:
            current = candidate
        if len(lines) >= max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    if len(lines) == max_lines and len(" ".join(lines)) < len(text):
        lines[-1] = lines[-1].rstrip(".") + "..."
    return lines


def svg_text_block(
    lines: list[str],
    *,
    x: int,
    y: int,
    size: int,
    fill: str,
    weight: int = 500,
    line_gap: int = 38,
) -> str:
    nodes = []
    for index, line in enumerate(lines):
        nodes.append(
            f'<text x="{x}" y="{y + index * line_gap}" text-anchor="middle" '
            f'font-family="Arial, Apple SD Gothic Neo, sans-serif" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}">{escape(line)}</text>'
        )
    return "\n".join(nodes)


def build_page_svg(story: dict[str, Any], page: dict[str, Any]) -> bytes:
    palette = [
        ("#f7d774", "#85d4ff", "#ff8fa3"),
        ("#c1f0c1", "#7ec8e3", "#ffcb77"),
        ("#ffd6e0", "#b8c0ff", "#8ecae6"),
        ("#fbe7a1", "#a7d7c5", "#f28482"),
        ("#d9ed92", "#99d98c", "#56cfe1"),
    ]
    page_number = int(page["page"])
    top, middle, accent = palette[(page_number - 1) % len(palette)]
    title_lines = wrap_text(str(story["title"]), 24, 2)
    page_text = wrap_text(str(page["text"]), 30, 4)
    visual_text = wrap_text(str(page["visual"]), 36, 3)
    moon_or_sun = "M512 138 L535 202 L604 206 L549 248 L566 314 L512 276 L458 314 L475 248 L420 206 L489 202 Z"
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{top}"/>
      <stop offset="0.55" stop-color="{middle}"/>
      <stop offset="1" stop-color="#ffffff"/>
    </linearGradient>
    <filter id="soft" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="8"/>
    </filter>
  </defs>
  <rect width="1024" height="1024" rx="42" fill="url(#bg)"/>
  <circle cx="194" cy="184" r="96" fill="#ffffff" opacity="0.52" filter="url(#soft)"/>
  <circle cx="812" cy="252" r="118" fill="#ffffff" opacity="0.38" filter="url(#soft)"/>
  <path d="{moon_or_sun}" fill="{accent}" stroke="#ffffff" stroke-width="8"/>
  <path d="M214 548 C340 490 454 504 512 590 C570 504 684 490 810 548 L810 732 C664 682 566 710 512 800 C458 710 360 682 214 732 Z" fill="#fffaf0" stroke="#986f43" stroke-width="12"/>
  <path d="M512 590 L512 800" stroke="#c79a63" stroke-width="9"/>
  <path d="M256 704 C364 668 458 692 512 800 C566 692 660 668 768 704" fill="none" stroke="#f0d3a1" stroke-width="8"/>
  <circle cx="360" cy="404" r="48" fill="#ffffff" opacity="0.75"/>
  <circle cx="422" cy="404" r="64" fill="#ffffff" opacity="0.78"/>
  <circle cx="496" cy="404" r="48" fill="#ffffff" opacity="0.75"/>
  <circle cx="660" cy="426" r="42" fill="#ffffff" opacity="0.68"/>
  <circle cx="708" cy="426" r="58" fill="#ffffff" opacity="0.7"/>
  <circle cx="772" cy="426" r="44" fill="#ffffff" opacity="0.68"/>
  {svg_text_block(title_lines, x=512, y=92, size=42, fill="#2f3645", weight=800, line_gap=48)}
  <text x="512" y="356" text-anchor="middle" font-family="Arial, Apple SD Gothic Neo, sans-serif" font-size="34" font-weight="800" fill="#2f3645">{page_number}페이지</text>
  {svg_text_block(page_text, x=512, y=842, size=28, fill="#2f3645", weight=700, line_gap=38)}
  {svg_text_block(visual_text, x=512, y=944, size=20, fill="#58606f", weight=500, line_gap=26)}
</svg>"""
    return svg.encode("utf-8")


class PageIllustratorAgent(BaseAgent):
    page_number: int = Field(ge=1, le=TOTAL_PAGES)

    async def _run_async_impl(
        self,
        ctx: InvocationContext,
    ) -> AsyncGenerator[Event, None]:
        theme = user_text_from_context(ctx)
        story = normalize_story(ctx.session.state.get(STORY_STATE_KEY), theme)
        page = story["pages"][self.page_number - 1]
        svg_bytes = build_page_svg(story, page)
        filename = (
            f"storybook_page_{self.page_number}_"
            f"{artifact_slug(str(story['title']))}.svg"
        )
        callback_context = CallbackContext(ctx)
        version = await callback_context.save_artifact(
            filename=filename,
            artifact=types.Part.from_bytes(
                data=svg_bytes,
                mime_type="image/svg+xml",
            ),
            custom_metadata={
                "page": self.page_number,
                "title": str(story["title"]),
                "visual": str(page["visual"]),
            },
        )
        image_info = {
            "page": self.page_number,
            "filename": filename,
            "version": version,
            "mime_type": "image/svg+xml",
            "visual": page["visual"],
        }
        callback_context.state[f"{IMAGE_STATE_PREFIX}{self.page_number}"] = image_info
        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            branch=ctx.branch,
            actions=callback_context.actions,
            content=types.Content(
                role="model",
                parts=[
                    types.Part.from_text(
                        text=(
                            f"이미지 {self.page_number}/{TOTAL_PAGES} 생성 완료: "
                            f"{filename} (Artifact v{version})"
                        )
                    )
                ],
            ),
        )


class StoryWriterFallbackAgent(BaseAgent):
    async def _run_async_impl(
        self,
        ctx: InvocationContext,
    ) -> AsyncGenerator[Event, None]:
        theme = user_text_from_context(ctx)
        story = fallback_story_from_theme(theme)
        callback_context = CallbackContext(ctx)
        callback_context.state[STORY_STATE_KEY] = json.dumps(story, ensure_ascii=False)
        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            branch=ctx.branch,
            actions=callback_context.actions,
            content=types.Content(
                role="model",
                parts=[
                    types.Part.from_text(
                        text=(
                            "스토리 작성 완료: "
                            f"{story['title']} ({TOTAL_PAGES}페이지)"
                        )
                    )
                ],
            ),
        )


class StorybookAssemblerAgent(BaseAgent):
    async def _run_async_impl(
        self,
        ctx: InvocationContext,
    ) -> AsyncGenerator[Event, None]:
        theme = user_text_from_context(ctx)
        story = normalize_story(ctx.session.state.get(STORY_STATE_KEY), theme)
        images = [
            ctx.session.state.get(f"{IMAGE_STATE_PREFIX}{page_number}")
            for page_number in range(1, TOTAL_PAGES + 1)
        ]
        if not all(isinstance(image, dict) for image in images):
            raise ValueError("Parallel Illustrator Agent did not create all five images.")

        lines = [
            f"# {story['title']}",
            "",
            f"테마: {theme}",
            "",
            "Workflow: SequentialAgent → Story Writer Agent → ParallelAgent(5 Illustrator Agents) → Final Assembler",
            "",
        ]
        for page in story["pages"]:
            image = images[int(page["page"]) - 1]
            lines.extend(
                [
                    f"## {page['page']}페이지",
                    "",
                    str(page["text"]),
                    "",
                    f"삽화 설명: {page['visual']}",
                    "",
                    f"Image Artifact: {image['filename']} (v{image['version']})",
                    "",
                ]
            )

        final_markdown = "\n".join(lines).strip()
        callback_context = CallbackContext(ctx)
        callback_context.state[FINAL_STATE_KEY] = final_markdown

        parts = [types.Part.from_text(text=final_markdown)]
        for image in images:
            artifact = await callback_context.load_artifact(str(image["filename"]))
            if artifact:
                parts.append(artifact)

        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            branch=ctx.branch,
            actions=callback_context.actions,
            content=types.Content(role="model", parts=parts),
        )


STORY_WRITER_INSTRUCTION = """
당신은 Story Writer Agent입니다.
사용자 입력을 어린이 동화책 테마로 보고, 정확히 5페이지짜리 한국어 동화책 초안을 작성하세요.

반드시 JSON만 반환하세요. 마크다운 코드블록은 쓰지 마세요.

스키마:
{
  "title": "짧은 한국어 제목",
  "pages": [
    {
      "page": 1,
      "text": "1-2개의 짧고 따뜻한 한국어 문장",
      "visual": "해당 페이지에 들어갈 삽화 설명"
    }
  ]
}

규칙:
- pages는 정확히 5개여야 합니다.
- page 값은 1부터 5까지 순서대로 작성합니다.
- text와 visual은 반드시 한국어로 작성합니다.
- 무섭거나 폭력적인 장면 없이 어린이에게 안전하고 다정하게 작성합니다.
- 같은 주인공이 5페이지 동안 이어지도록 합니다.
""".strip()


if should_use_llm_writer():
    story_writer_agent = LlmAgent(
        name="StoryWriterAgent",
        description="5페이지 어린이 동화를 JSON으로 작성하고 Agent State에 저장합니다.",
        model=build_story_model(),
        instruction=STORY_WRITER_INSTRUCTION,
        output_key=STORY_STATE_KEY,
        before_agent_callback=progress_callback("스토리 작성 중..."),
        after_agent_callback=progress_callback("스토리 작성 완료"),
        on_model_error_callback=story_writer_error_callback,
    )
else:
    story_writer_agent = StoryWriterFallbackAgent(
        name="StoryWriterAgent",
        description="5페이지 어린이 동화를 작성하고 Agent State에 저장합니다.",
        before_agent_callback=progress_callback("스토리 작성 중..."),
        after_agent_callback=progress_callback("스토리 작성 완료"),
    )

parallel_illustrator_agent = ParallelAgent(
    name="ParallelIllustratorAgent",
    description="5개의 페이지 삽화를 동시에 생성해 Artifact로 저장합니다.",
    sub_agents=[
        PageIllustratorAgent(
            name=f"IllustratorPage{page_number}Agent",
            description=f"{page_number}페이지 삽화를 SVG Artifact로 생성합니다.",
            page_number=page_number,
            before_agent_callback=progress_callback(
                f"이미지 {page_number}/{TOTAL_PAGES} 생성 중..."
            ),
            after_agent_callback=progress_callback(
                f"이미지 {page_number}/{TOTAL_PAGES} 생성 완료"
            ),
        )
        for page_number in range(1, TOTAL_PAGES + 1)
    ],
    before_agent_callback=progress_callback("5개의 삽화를 병렬 생성 중..."),
    after_agent_callback=progress_callback("5개의 삽화 생성 완료"),
)

final_assembler_agent = StorybookAssemblerAgent(
    name="StorybookAssemblerAgent",
    description="스토리 텍스트와 이미지 Artifact를 최종 동화책 출력으로 조립합니다.",
    before_agent_callback=progress_callback("완성된 동화책 조립 중..."),
    after_agent_callback=progress_callback("완성된 동화책 준비 완료"),
)

root_agent = SequentialAgent(
    name="StoryBookMakerWorkflowAgent",
    description=(
        "Workflow Agent 기반 어린이 동화책 파이프라인입니다. "
        "SequentialAgent가 Writer→Parallel Illustrator→Assembler 흐름을 관리합니다."
    ),
    sub_agents=[
        story_writer_agent,
        parallel_illustrator_agent,
        final_assembler_agent,
    ],
    before_agent_callback=progress_callback("Story Book Maker 파이프라인 시작"),
    after_agent_callback=progress_callback("Story Book Maker 파이프라인 완료"),
)
