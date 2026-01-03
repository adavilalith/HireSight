import psycopg2
from psycopg2.extras import execute_values
import json

class PostgresClient:
    def __init__(self, connection_uri: str):
        print("trying to connect at:",connection_uri)
        self.conn = psycopg2.connect(connection_uri)
        self._create_table()

    def _create_table(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS jobs_raw (
                    id SERIAL PRIMARY KEY,
                    role_searched TEXT NOT NULL,
                    location_searched TEXT NOT NULL,
                        
                    raw_json JSONB NOT NULL,
                    full_description_html TEXT,
                        
                    crawled BOOLEAN DEFAULT FALSE,
                    crawl_attempts INTEGER DEFAULT 0,
                    last_crawl_at TIMESTAMP,
                        
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            self.conn.commit()

    def save_jobs(self, jobs: list, role: str, location: str):
        """Saves a list of job dicts using an UPSERT strategy."""
        data = [
            (role, location, json.dumps(j)) 
            for j in jobs
        ]
        
        query = """
            INSERT INTO jobs_raw (role_searched, location_searched, raw_json)
            VALUES %s;
        """
        
        with self.conn.cursor() as cur:
            execute_values(cur, query, data)
            self.conn.commit()
            print(f"Successfully synced {len(data)} jobs to Postgres.")

    def get_pending_jobs(self, limit=10):
        """Fetches jobs that haven't been crawled yet."""
        query = "SELECT id, raw_json->'apply_options'->0->>'link' FROM jobs_raw WHERE crawled = FALSE LIMIT %s"
        with self.conn.cursor() as cur:
            cur.execute(query, (limit,))
            return cur.fetchall() # Returns list of (job_id, url)

    def update_job_description(self, id: str, markdown: str):
        """Updates a job record with its crawled content."""
        query = """
            UPDATE jobs_raw 
            SET full_description_markdown = %s, 
                crawled = TRUE, 
                last_crawl_at = CURRENT_TIMESTAMP
            WHERE id = %s;
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (markdown, id))
            self.conn.commit()

    def close(self):
        self.conn.close()