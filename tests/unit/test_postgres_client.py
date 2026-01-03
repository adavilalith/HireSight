import pytest

@pytest.mark.unit
def test_save_jobs_insertion(db_client):
    """Test that jobs are successfully inserted into the DB"""
    sample_jobs = [
        {"job_id": "test_1", "title": "Data Analyst", "company": "TechCorp"},
        {"job_id": "test_2", "title": "BI Engineer", "company": "DataInc"}
    ]
    
    db_client.save_jobs(sample_jobs, "Data Analyst", "Hyderabad, Telangana, India")
    
    with db_client.conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM jobs_raw WHERE role_searched = 'Data Analyst';")
        count = cur.fetchone()[0]
    
    assert count == 2

@pytest.mark.unit
def test_upsert_logic(db_client):
    """Test that duplicate job_ids do not create duplicate rows"""
    duplicate_job = [{"job_id": "unique_123", "title": "Duplicate Test"}]
    
    # Run insertion twice
    db_client.save_jobs(duplicate_job, "Tester", "Remote")
    db_client.save_jobs(duplicate_job, "Tester", "Remote")
    
    with db_client.conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM jobs_raw WHERE job_id = 'unique_123';")
        count = cur.fetchone()[0]
    
    assert count == 1  # Should still be 1 despite two calls