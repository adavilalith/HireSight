import pytest

@pytest.mark.unit
def test_save_jobs_insertion(db_client):
    """Test that jobs are successfully inserted into the DB"""
    sample_jobs = [
        {"title": "Data Analyst", "company": "TechCorp"},
        {"title": "BI Engineer", "company": "DataInc"}
    ]
    
    db_client.save_jobs(sample_jobs, "Data Analyst", "Hyderabad, Telangana, India")
    
    with db_client.conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM jobs_raw WHERE role_searched = 'Data Analyst';")
        count = cur.fetchone()[0]
    
    assert count == 2
