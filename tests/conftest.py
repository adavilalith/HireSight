import pytest
import os
from hiresight.db.postgres_client import PostgresClient

@pytest.fixture(scope="module")
def db_client():
    url = os.getenv("POSTGRES_TEST_URL", "")
    client = PostgresClient(url)
    yield client

    with client.conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE jobs_raw,jobs_parsed;")
        client.conn.commit()
    client.close()