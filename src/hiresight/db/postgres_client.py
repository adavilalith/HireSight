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
                external_id TEXT UNIQUE NOT NULL, -- The job_id from SerpApi
                role_searched TEXT NOT NULL,
                location_searched TEXT NOT NULL,
                raw_json JSONB NOT NULL,
                full_description_markdown TEXT,
                crawled BOOLEAN DEFAULT FALSE,
                
                -- status options: 'pending', 'processing', 'completed', 'failed'
                processing_status TEXT DEFAULT 'pending',
                
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
        """
        Saves job dicts using an UPSERT strategy.
        If external_id exists, we update the raw_json and reset status if needed.
        """
        data = [
            (
                j.get('job_id'),       # external_id
                role,                  # role_searched
                location,              # location_searched
                json.dumps(j)          # raw_json
            ) 
            for j in jobs if j.get('job_id')
        ]
        
        # UPSERT Query: Update raw_json if external_id already exists
        query = """
            INSERT INTO jobs_raw (external_id, role_searched, location_searched, raw_json)
            VALUES %s
            ON CONFLICT (external_id) 
            DO NOTHING;
        """
        
        with self.conn.cursor() as cur:
            execute_values(cur, query, data)
            self.conn.commit()
            print(f"Successfully upserted {len(data)} jobs to Postgres.")

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

    def get_job_with_lock(self):
        """
        Atomically finds one pending job, locks it, and marks it as processing.
        Returns (db_id, markdown, cursor) so the caller can commit later.
        """
        # We create a specific cursor for this transaction
        cur = self.conn.cursor()
        try:
            query = """
                SELECT id, full_description_markdown 
                FROM jobs_raw 
                WHERE crawled = TRUE 
                AND processing_status = 'pending'
                ORDER BY created_at ASC
                LIMIT 1;
            """
            cur.execute(query)
            row = cur.fetchone()
            
            if row:
                job_id = row[0]
                # Immediately mark as processing so other containers don't see it
                cur.execute(
                    "UPDATE jobs_raw SET processing_status = 'processing' WHERE id = %s", 
                    (job_id,)
                )
                return row[0], row[1], cur
            
            cur.close()
            return None, None, None
        except Exception as e:
            self.conn.rollback()
            cur.close()
            raise e
            
    def finalize_job(self, cur, job_id, result):
        """Saves parsed data and marks raw job as completed in one transaction."""
        try:
            # 1. Save to parsed table using the existing cursor
            self.save_parsed_job_with_cursor(cur, job_id, result)
            
            # 2. Update status to completed
            cur.execute(
                "UPDATE jobs_raw SET processing_status = 'completed' WHERE id = %s", 
                (job_id,)
            )
            
            # 3. Commit the whole transaction
            self.conn.commit()
            cur.close()
        except Exception as e:
            self.conn.rollback()
            cur.close()
            raise e

    def save_parsed_job_with_cursor(self, cur, raw_id, job_data):
        """Helper to use an existing transaction cursor."""
        query = """
            INSERT INTO jobs_parsed (
                job_raw_id, role, job_type, seniority, is_remote, 
                salary_min, salary_max, salary_currency, 
                tech_stack, soft_skills, responsibilities, education_required
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        values = (
            raw_id, job_data.role, job_data.job_type, job_data.seniority, 
            job_data.is_remote, job_data.salary_min, job_data.salary_max, 
            job_data.salary_currency, Json(job_data.tech_stack),      
            Json(job_data.soft_skills), Json(job_data.responsibilities), 
            job_data.education_required
        )
        cur.execute(query, values)

    def close(self):
        self.conn.close()
    
