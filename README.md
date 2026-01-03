# HireSight: Job Market Intelligence Pipeline 🚀

HireSight is an automated data engine that transforms unstructured job postings into high-fidelity, structured datasets. Built for scale, it uses a **tiered LLM extraction** strategy and **asynchronous processing** to handle bulk data without hitting rate limits.

## 🛠 current Status: Local Stage

Currently, the core engine is operational in a local environment. The next phase involves migrating orchestration to **GitHub Actions** and storage to **Neon (Serverless Postgres)** for 24/7 background processing.

* [x] Discovery Layer (SerpApi): Automated lead generation using google_jobs engine.
* [x] Deep Crawling (Crawl4AI): High-speed, AI-ready markdown extraction with automated HTML cleaning.
* [x] Pydantic V2 Schemas with Type Coercion (LPA to Int, Boolean logic)
* [x] Asynchronous Multi-LLM Parser (Llama 3.3 70B + 3.1 8B)
* [x] Asyncio Semaphore for Rate Limit Control
* [x] Local PostgreSQL Integration
* [ ] GitHub Actions Staggered Cron Jobs
* [ ] Neon Cloud DB Migration
* [ ] Multi-API Key Rotation Logic

## 🏗️ Technical Architecture

* **Orchestration:** `asyncio` for concurrent LLM processing.
* **Intelligence:** * **Core Extraction:** Llama 3.3 70B (Logic & Salary standardization).
* **Skill Extraction:** Llama 3.1 8B (High-speed list generation).


* **Data Integrity:** Pydantic `BeforeValidator` layers to clean "messy" LLM strings into strict Python/SQL types.
* **Package Management:** `uv` (Extremely fast Python dependency resolver).

## 🚀 Setup (Local)

### Prerequisites

* [uv](https://github.com/astral-sh/uv) installed.
* Local PostgreSQL instance.
* Groq API Key.

### Installation

1. **Clone the repo:**
```bash
git clone https://github.com/yourusername/hiresight.git
cd hiresight

```


2. **Sync environment with uv:**
```bash
uv sync

```


3. **Environment Variables:**
Create a `.env` file:
```env
POSTGRES_URL="postgresql://user:pass@localhost:5432/hiresight"
GROQ_API_KEY="your_key_here"

```



## 🧪 Running Tests

The project utilizes `pytest` with `pytest-asyncio` for testing asynchronous logic.

```bash
# Run unit tests (Schemas & Parsers)
uv run pytest tests/unit

# Run integration tests (Database)
uv run pytest tests/integration

```

## 🛤️ Roadmap

1. **Cloud Migration:** Move local PG to **Neon** for serverless scaling.
2. **GitHub Actions:** Implement `.github/workflows/process.yml` to run hourly batch processing.
3. **Key Rotation:** Add logic to cycle through multiple `GROQ_KEYS` to maximize throughput.
4. **Local Inference:** Add **Ollama** fallback support for Llama 3.3 70B.
