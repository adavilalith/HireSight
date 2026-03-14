

# HireSight: Job Market Intelligence Pipeline 

HireSight is an automated data engine that transforms unstructured job postings into high-fidelity, structured datasets. Built for scale, it uses a **Bronze-Silver Medallion Architecture**, **tiered LLM extraction**, and **transaction-safe concurrency** to handle bulk job market analysis without hitting rate limits.

## Technical Architecture

HireSight operates as a two-stage asynchronous pipeline:

### 1. The Bronze Pipeline (Ingestion)

* **Discovery:** Uses SerpApi to find job leads based on a dynamic `jobs_config.json`.
* **Deduplication:** Uses an `external_id` (SerpApi Job ID) with `ON CONFLICT DO NOTHING` to ensure a clean source of truth.
* **Deep Crawl:** Utilizes **Crawl4AI** to convert job URLs into clean, AI-ready Markdown.

### 2. The Silver Pipeline (Structured Extraction)

* **Concurrency:** Implements `FOR UPDATE SKIP LOCKED` transactions, allowing multiple workers to process jobs simultaneously without collisions.
* **Tiered Intelligence:**
* **Llama 3.3 70B:** Handles complex reasoning, salary extraction, and currency standardization.
* **Llama 3.1 8B:** Optimized for high-speed, token-efficient extraction of tech stacks and responsibilities.


* **Data Integrity:** Pydantic V2 validation ensures LLM outputs are coerced into strict Python/SQL types.

---

## Orchestration & Automation

HireSight is designed to be "set and forget." You can automate the pipelines using two primary methods:

### Option A: GitHub Actions (Cloud Native)

Perfect for 24/7 background processing on public repositories.

* **Bronze:** Runs every 15 days to fetch fresh leads.
* **Silver:** Runs every 7 days, processing the queue in a 6-hour "slow-burn" to respect API rate limits.
* **Note:** Requires a hosted database (e.g., Neon.tech).

### Option B: Local Crontab (Self-Hosted)

Ideal for running on a local server or laptop.

```bash
# 1. Run Bronze Pipeline every 1st and 15th at 2:00 AM
0 2 1,15 * * cd /path/to/project && docker compose run --rm bronze-pipeline

# 2. Run Silver Pipeline every Sunday at 3:00 AM
0 3 * * 0 cd /path/to/project && docker compose run --rm silver-pipeline

```

---

## 🛠 Setup Instructions

### 1. Prerequisites

* [uv](https://github.com/astral-sh/uv) (The only Python tool you'll need).
* Docker & Docker Compose.
* API Keys: Groq (LLM) and SerpApi (Scraping).

### 2. Installation

```bash
git clone https://github.com/yourusername/hiresight.git
cd hiresight

# Sync dependencies exactly to the frozen lockfile
uv sync --frozen

```

### 3. Environment Configuration

Create a `.env` file in the root directory:

```env
# Database
POSTGRES_URL="postgresql://admin:password@localhost:5432/hiresight"

# API Keys
GROQ_API_KEY="gsk_..."
SERPAPI_KEY="..."

```

### 4. Local Deployment

```bash
# Spin up the database and services
docker compose up -d

```

---

## Development & Testing

We use `pytest` with `pytest-asyncio` for ensuring logic remains robust during schema changes.

```bash
# Run all tests
uv run pytest

# Run specific integration tests
uv run pytest tests/integration

```
---

### License

This project is open-source and available under the MIT License. (see [LICENSE](https://github.com/adavilalith/HireSight/LICENSE)).

---
