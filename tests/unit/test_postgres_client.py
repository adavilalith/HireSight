import pytest
from unittest.mock import MagicMock
from psycopg2.extras import Json
from hiresight.db.postgres_client import PostgresClient

@pytest.mark.unit
def test_save_jobs_insertion(db_client):
    """Verifies that the Scraper can save multiple raw job objects."""
    sample_jobs = [
        {"link": "https://link1.com", "title": "Data Analyst"},
        {"link": "https://link2.com", "title": "BI Engineer"}
    ]
    
    db_client.save_jobs(sample_jobs, "Data Analyst", "Hyderabad")
    
    with db_client.conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM jobs_raw WHERE location_searched = 'Hyderabad';")
        count = cur.fetchone()[0]
    
    assert count == 2

@pytest.mark.unit
def test_update_job_description(db_client):
    """Verifies that the Crawler can attach markdown to a raw record."""
    # First, insert a dummy job
    db_client.save_jobs([{"title": "Test"}], "Dev", "Loc")
    
    with db_client.conn.cursor() as cur:
        cur.execute("SELECT id FROM jobs_raw LIMIT 1;")
        job_id = cur.fetchone()[0]
    
    # Update with markdown
    test_markdown = "# Job Description\nMust know Python."
    db_client.update_job_description(job_id, test_markdown)
    
    with db_client.conn.cursor() as cur:
        cur.execute("SELECT full_description_markdown, crawled FROM jobs_raw WHERE id = %s;", (job_id,))
        row = cur.fetchone()
    
    assert row[0] == test_markdown
    assert row[1] is True # crawled flag should be true

@pytest.mark.unit
def test_save_parsed_job(db_client):
    """Verifies that the Processor can save structured data into the Silver table."""
    # 1. Setup: Create a raw record to satisfy Foreign Key
    db_client.save_jobs([{"title": "Analyst"}], "Analyst", "Bangalore")
    with db_client.conn.cursor() as cur:
        cur.execute("SELECT id FROM jobs_raw LIMIT 1;")
        raw_id = cur.fetchone()[0]

    # 2. Mock a Pydantic JobExtraction object
    mock_job = MagicMock()
    mock_job.role = "Senior Data Analyst"
    mock_job.job_type = "Full-time"
    mock_job.seniority = "Senior"
    mock_job.is_remote = True
    mock_job.salary_min = 1200000
    mock_job.salary_max = 1800000
    mock_job.salary_currency = "INR"
    mock_job.tech_stack = ["Python", "SQL", "Tableau"]
    mock_job.soft_skills = ["Storytelling"]
    mock_job.responsibilities = ["Analyze data"]
    mock_job.education_required = "Bachelors"

    # 3. Save to Silver table
    db_client.save_parsed_job(raw_id, mock_job)
    
    with db_client.conn.cursor() as cur:
        cur.execute("SELECT role, tech_stack FROM jobs_parsed WHERE job_raw_id = %s;", (raw_id,))
        row = cur.fetchone()
    
    assert row[0] == "Senior Data Analyst"
    assert "Python" in row[1] # tech_stack is returned as a list thanks to psycopg2/JSONB