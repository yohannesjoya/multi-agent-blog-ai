# Multi-Agent Blog AI

Multi-Agent Blog AI is a FastAPI service that turns source links into a polished, Medium-style blog post. It uses a CrewAI workflow with specialized agents for research cleanup, content planning, writing, and editorial review, while Firecrawl extracts clean markdown content from the provided URLs.

## Features

- Scrapes main article content from one or more source links
- Cleans and organizes raw content into useful research notes
- Builds a structured content plan with audience, outline, SEO keywords, and sources
- Generates a markdown blog post from the plan
- Runs an editor pass for grammar, structure, tone, and publication readiness
- Exposes a simple HTTP API for blog generation

## Project Structure

```text
.
├── app.py          # FastAPI app and CrewAI workflow entry point
├── researcher.py   # Research cleanup agent and task
├── planner.py      # Content planning agent and task
├── writer.py       # Blog writing agent and task
├── editor.py       # Editorial review agent and task
├── scrapper.py     # Firecrawl scraping and optional markdown saving helpers
└── packages.txt    # Python dependencies
```

## How It Works

1. A client sends a topic and source links to `POST /api/v1/generate`.
2. `scrapper.py` uses Firecrawl to extract the main markdown content from each link.
3. The extracted content is passed through a CrewAI pipeline:
   - **Researcher** cleans and chunks the raw content.
   - **Planner** creates the content strategy and outline.
   - **Writer** drafts the blog post in markdown.
   - **Editor** reviews and polishes the final article.
4. The API returns the generated markdown content and a publication timestamp.

## Requirements

- Python 3.10 or newer
- Firecrawl API key
- OpenAI-compatible API provider key and endpoint

The app is currently configured to read a Groq API key through `GROQ_API_KEY`, while setting OpenAI-compatible environment variables for CrewAI.

## Installation

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r packages.txt
```

## Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
API_BASE=your_openai_compatible_api_base_url
MODEL=your_model_name
CRAWLER_API_KEY=your_firecrawl_api_key
```

Example model values depend on your provider. For Groq, use the API base and model name provided in your Groq dashboard.

## Running the API

Start the FastAPI server with Uvicorn:

```bash
uvicorn app:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Health check:

```bash
curl http://127.0.0.1:8000/
```

Expected response:

```json
{
  "hello": "world"
}
```

## Generate a Blog Post

Send a `POST` request to `/api/v1/generate`:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {
      "topic": "The future of AI agents in software development",
      "links": [
        "https://example.com/source-article-1",
        "https://example.com/source-article-2"
      ]
    }
  }'
```

Example response shape:

```json
{
  "content": "# Generated blog post in markdown...",
  "publicationDate": "20260628_153045"
}
```

## Notes

- Generated markdown is returned in the API response.
- `scrapper.py` includes a `save_data` helper for saving markdown files locally, but saving generated posts is currently commented out in `app.py`.
- The API currently allows all CORS origins. Tighten this before deploying to production.
- Do not commit your `.env` file or API keys.

## Troubleshooting

If scraping fails, confirm that `CRAWLER_API_KEY` is valid and that the source URL is publicly accessible.

If the CrewAI workflow fails, confirm that `GROQ_API_KEY`, `API_BASE`, and `MODEL` match your OpenAI-compatible provider settings.

If dependencies fail to install, make sure the virtual environment is active and that you are using a compatible Python version.
