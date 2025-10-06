# HireSight

HireSight is a complete end-to-end **job intelligence pipeline** that collects job postings, crawls details, extracts structured features, and visualizes insights.  
It demonstrates scalable **data engineering + NLP + visualization** skills and serves as a strong portfolio project.

---

## 🚀 Features
- **Job Collection**
  - Uses **Google Jobs API** (Talent Solution) to fetch job listings by role, location, and filters.
  - (Alternative fallbacks: SerpAPI or Playwright scraping).
- **Crawling**
  - Fetches job posting pages with **Crawl4AI**.
- **Parsing & Extraction**
  - Uses **LLMs (via Groq/OpenRouter)** to extract structured fields:
    - `company`, `domain`, `skills`, `salary`, `experience`, `gender`, `location`, `job_type`.
- **Data Storage**
  - **PostgreSQL**: Stores raw job listing info.
  - **MongoDB**: Stores parsed and enriched structured data.
- **Visualization**
  - Interactive **Tableau dashboards** for insights:
    - In-demand skills by location
    - Salary distribution
    - Job type breakdown (remote/hybrid/onsite)
    - Company hiring trends
- **Scalability**
  - Modular design: all steps can run inside a single container.
  - Supports parallel queries by job type/location.
  - Easy to scale with multiple containers or task queues (Celery, Kafka, RabbitMQ).

---

## 🛠️ Tech Stack
- **Data Collection**: Google Jobs API / SerpAPI / Playwright  
- **Crawling**: Crawl4AI  
- **LLM Parsing**: LangChain + Groq (via OpenRouter)  
- **Databases**: PostgreSQL + MongoDB  
- **Visualization**: Tableau  
- **Containerization**: Docker  

---

## 📂 Project Structure
```
HireSight/
│
├── crawler/                # Crawl4AI scripts to fetch job descriptions
├── parser/                 # LLM-based job parser
├── playwright/             # Optional Playwright scraper
├── db/                     # Database setup & schema
│   ├── postgres/           # Raw job listings
│   └── mongo/              # Parsed structured data
├── tableau/                # Tableau dashboards & exports
├── jobs.json               # Example raw jobs data
├── crawled_jobs.json       # Example crawled job postings
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

---

## ⚡ Workflow
1. **Collect Jobs**  
   Query Google Jobs API with role & location → save results to PostgreSQL.  
2. **Crawl**  
   Crawl each job page with Crawl4AI → store content.  
3. **Parse**  
   Use Groq LLM → extract structured JSON fields → save to MongoDB.  
4. **Visualize**  
   Tableau dashboards fetch data → interactive insights.  

---

## 📊 Example Parsed Output
```json
{
  "company": "TechCorp",
  "domain": "Software",
  "skills": ["Python", "Django", "SQL"],
  "salary": "8-12 LPA",
  "experience": "2-4 years",
  "gender": "Any",
  "location": "Hyderabad",
  "job_type": "Hybrid"
}
```

---

## 🔑 Setup & Usage

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/HireSight.git
cd HireSight
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file:
```
OPENROUTER_API_KEY=your_key_here
GOOGLE_APPLICATION_CREDENTIALS=./path/to/credentials.json
POSTGRES_URL=postgresql://user:pass@localhost:5432/hiresight
MONGO_URI=mongodb://localhost:27017/hiresight
```

### 4. Run Pipeline
```bash
python crawler/fetch_jobs.py
python crawler/crawl_jobs.py
python parser/parse_jobs.py
```

### 5. Tableau Visualization
- Connect Tableau to MongoDB/PostgreSQL extracts.
- Load provided `tableau/` dashboards for analysis.

---

## 📈 Tableau Dashboards
- **Skill Trends by City**  
- **Salary Insights**  
- **Job Type Distribution**  
- **Top Hiring Companies**

---

