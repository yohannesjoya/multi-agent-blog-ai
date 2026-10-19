import os
import threading
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

# CrewAI 0.41 talks to any OpenAI-compatible endpoint through these three vars.
os.environ["OPENAI_API_BASE"] = os.getenv("API_BASE", "https://api.groq.com/openai/v1")
os.environ["OPENAI_MODEL_NAME"] = os.getenv("MODEL", "openai/gpt-oss-120b")
os.environ["OPENAI_API_KEY"] = os.getenv("GROQ_API_KEY", "")

from crewai import Crew
import openai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field, HttpUrl

from editor import edit, editor
from planner import plan, planner
from researcher import research, researcher
from scrapper import ScrapeError, scrape_data
from writer import write, writer

crew = Crew(
    agents=[researcher, planner, writer, editor],
    tasks=[research, plan, write, edit],
    verbose=2,
)

DAILY_LIMIT = int(os.getenv("DAILY_LIMIT", "20"))
MAX_LINKS = 2  # Groq free tier: 8k tokens/min per request, so keep the crew's context small

app = FastAPI(title="Multi-Agent Blog AI")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Daily cap (in-memory; one container, free-tier demo) -----------------

_cap_lock = threading.Lock()
_cap_day = ""
_cap_used = 0


def _take_daily_slot() -> int:
    """Reserve one generation for today. Returns remaining, raises 429 when out."""
    global _cap_day, _cap_used
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with _cap_lock:
        if _cap_day != today:
            _cap_day, _cap_used = today, 0
        if _cap_used >= DAILY_LIMIT:
            raise HTTPException(
                status_code=429,
                detail=f"Demo limit of {DAILY_LIMIT} posts per day reached. Try again tomorrow (UTC).",
            )
        _cap_used += 1
        return DAILY_LIMIT - _cap_used


# --- API ------------------------------------------------------------------


class GenerateInputs(BaseModel):
    topic: str = Field(min_length=3, max_length=200)
    links: list[HttpUrl] = Field(min_length=1, max_length=MAX_LINKS)


class GenerateRequest(BaseModel):
    inputs: GenerateInputs


@app.post("/api/v1/generate")
def generate(body: GenerateRequest):
    remaining = _take_daily_slot()

    content = []
    for link in body.inputs.links:
        try:
            content.append(scrape_data(str(link)))
        except ScrapeError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        result = crew.kickoff(inputs={"topic": body.inputs.topic, "content": content})
    except openai.APIStatusError as exc:
        # Free-tier limits and model outages reach here; say so instead of a bare 500.
        raise HTTPException(
            status_code=502,
            detail=f"The language model refused the request ({exc.status_code}). Try shorter sources or wait a minute.",
        ) from exc
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    return JSONResponse(
        content={
            "content": str(result),
            "publicationDate": timestamp,
            "remainingToday": remaining,
        },
        status_code=201,
    )


@app.get("/health")
def health():
    return {"status": "ok", "model": os.environ["OPENAI_MODEL_NAME"]}


# --- Minimal demo page ----------------------------------------------------

INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Multi-Agent Blog AI</title>
<style>
  :root { color-scheme: light dark; }
  body { font-family: system-ui, sans-serif; max-width: 760px; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; }
  h1 { margin-bottom: .25rem; }
  .sub { color: #777; margin-top: 0; }
  label { display: block; font-weight: 600; margin-top: 1rem; }
  input, textarea { width: 100%; padding: .6rem; font: inherit; box-sizing: border-box; margin-top: .3rem; }
  button { margin-top: 1rem; padding: .7rem 1.2rem; font: inherit; cursor: pointer; }
  button:disabled { opacity: .6; cursor: wait; }
  #status { margin-top: 1rem; color: #777; }
  #out { white-space: pre-wrap; border: 1px solid #8884; padding: 1rem; border-radius: 8px; margin-top: 1rem; display: none; }
  .links a { margin-right: 1rem; }
</style>
</head>
<body>
<h1>Multi-Agent Blog AI</h1>
<p class="sub">Paste 1–2 article links and a topic. Four agents (researcher, planner, writer, editor) turn them into a Medium-style post. Takes 1–3 minutes.</p>
<p class="links"><a href="https://github.com/yohannesjoya/multi-agent-blog-ai">Source</a><a href="/docs">API docs</a><a href="https://yohannes-desta.vercel.app">Author</a></p>
<form id="f">
  <label>Topic<input name="topic" required minlength="3" placeholder="The future of AI agents in software development"></label>
  <label>Source links (one per line, max 2)<textarea name="links" rows="3" required placeholder="https://example.com/article"></textarea></label>
  <button id="go" type="submit">Generate post</button>
</form>
<div id="status"></div>
<div id="out"></div>
<script>
const f = document.getElementById('f'), go = document.getElementById('go'),
      st = document.getElementById('status'), out = document.getElementById('out');
f.addEventListener('submit', async (e) => {
  e.preventDefault();
  const topic = f.topic.value.trim();
  const links = f.links.value.split('\\n').map(s => s.trim()).filter(Boolean).slice(0, 2);
  go.disabled = true; out.style.display = 'none'; st.textContent = 'Scraping sources and running the crew…';
  try {
    const r = await fetch('/api/v1/generate', { method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ inputs: { topic, links } }) });
    const data = await r.json();
    if (!r.ok) { st.textContent = 'Error: ' + (data.detail?.[0]?.msg || data.detail || r.status); return; }
    st.textContent = 'Done. ' + data.remainingToday + ' demo runs left today.';
    out.textContent = data.content; out.style.display = 'block';
  } catch (err) { st.textContent = 'Request failed: ' + err; }
  finally { go.disabled = false; }
});
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def home():
    return INDEX_HTML
