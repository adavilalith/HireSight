import psycopg2
from psycopg2.extras import execute_values,Json
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
                    full_description_markdown TEXT,
                        
                    crawled BOOLEAN DEFAULT FALSE,
                    crawl_attempts INTEGER DEFAULT 0,
                    last_crawl_at TIMESTAMP,
                        
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Silver Layer (Structured Analytics Data)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS jobs_parsed (
                    id SERIAL PRIMARY KEY,
                    job_raw_id INTEGER REFERENCES jobs_raw(id) ON DELETE CASCADE,
                    
                    -- Categorical Fields
                    role TEXT,
                    job_type TEXT,
                    seniority TEXT,
                    is_remote BOOLEAN,
                    
                    -- Numerical/Currency Fields
                    salary_min INTEGER,
                    salary_max INTEGER,
                    salary_currency TEXT,
                    
                    -- List/Array Fields (JSONB)
                    tech_stack JSONB,
                    soft_skills JSONB,
                    responsibilities JSONB,
                    
                    -- Other metadata
                    education_required TEXT,
                    parsed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Optimization: GIN Index for fast skill searching
                CREATE INDEX IF NOT EXISTS idx_tech_stack ON jobs_parsed USING GIN (tech_stack);
                CREATE INDEX IF NOT EXISTS idx_role ON jobs_parsed (role);
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
        query = "SELECT id, raw_json->'apply_options' FROM jobs_raw WHERE crawled = FALSE LIMIT %s"
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

    def get_unparsed_jobs(self, limit=10):
        """Fetches markdown that hasn't been processed by the LLM yet."""
        query = """
            SELECT id, full_description_markdown 
            FROM jobs_raw 
            WHERE crawled = TRUE 
            AND id NOT IN (SELECT job_raw_id FROM jobs_parsed)
            LIMIT %s;
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (limit,))
            return cur.fetchall()

    def save_parsed_job(self, raw_id: int, job_data):
        """
        Saves the Pydantic JobExtraction object to the Silver table.
        Using the Json adapter ensures Pydantic lists -> Postgres JSONB.
        """
        query = """
            INSERT INTO jobs_parsed (
                job_raw_id, role, job_type, seniority, is_remote, 
                salary_min, salary_max, salary_currency, 
                tech_stack, soft_skills, responsibilities, education_required
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        
        values = (
            raw_id,
            job_data.role,
            job_data.job_type,
            job_data.seniority,
            job_data.is_remote,
            job_data.salary_min,
            job_data.salary_max,
            job_data.salary_currency,
            Json(job_data.tech_stack),      
            Json(job_data.soft_skills),     
            Json(job_data.responsibilities),
            job_data.education_required
        )
        
        with self.conn.cursor() as cur:
            cur.execute(query, values)
            self.conn.commit()

    def close(self):
        self.conn.close()