import asyncio
from os import sync
from typing import Dict, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from hiresight.processors.schemas import JobExtraction, CoreInfoSchema, SkillSetSchema

class JobParser:
    # 12,000 TPM limit / 2 (concurrent calls) = 6,000 tokens per call.
    # 6,000 tokens * 3.5 characters (conservative) = ~21,000 characters.
    # We'll set a safe buffer at 15,000 chars to account for prompt overhead.
    MAX_CHARS = 30000
    def __init__(self,max_concurrent=2):
        # 70B for the logic-heavy core info
        self.bouncer = asyncio.Semaphore(max_concurrent)
        self.core_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
        self.skill_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
        # Prompt 1: The Core Info (Identity & Money)
        self.core_prompt = ChatPromptTemplate.from_template(
            """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
            You are a data extraction bot. Your output must be a single, valid JSON object.
            
            REQUIRED JSON KEYS:
            - role (string)
            - job_type (string: "Full-time", "Contract", etc.)
            - seniority (string: "Junior", "Mid", "Senior", "Lead")
            - is_remote (boolean: true or false)
            - salary_min (integer or null)
            - salary_max (integer or null)
            - salary_currency (string: default "INR")
            - education_required (string or null)

            RULES:
            1. Do NOT include any preamble or explanation.
            2. Do NOT use markdown code blocks (no ```json).
            3. Ensure is_remote is a boolean (true/false) and salaries are integers.
            <|eot_id|>
            <|start_header_id|>user<|end_header_id|>
            EXTRACT FROM THIS TEXT:
            {markdown}
            <|eot_id|>
            <|start_header_id|>assistant<|end_header_id|>"""
        )
        # Prompt 2: The Skillset (Tools & Tasks)
        self.skill_prompt = ChatPromptTemplate.from_template(
            """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
            You are a specialized JSON extraction bot. 
            Respond ONLY with a valid JSON object matching this schema:
            {{
                "tech_stack": ["list of tools"],
                "soft_skills": ["list of skills"],
                "responsibilities": ["list of duties"]
            }}
            
            RULES:
            1. Keep tech tools specific (e.g., 'Python', not 'Software').
            2. Extract at most 15 tech items and 7 responsibilities to ensure quality.
            <|eot_id|>
            <|start_header_id|>user<|end_header_id|>
            JOB CONTENT:
            {markdown}
            <|eot_id|>
            <|start_header_id|>assistant<|end_header_id|>"""
        )
    def _truncate_markdown(self, text: str, limit: int = MAX_CHARS) -> str:
        """Simple cutoff to stay within Groq TPM limits."""
        if len(text) > limit:
            print(f"✂️ Truncating input from {len(text)} to {limit} chars.")
            return text[:limit]
        return text

    async def _extract_core(self, markdown: str) -> CoreInfoSchema:
        # Use truncated text
        safe_markdown = self._truncate_markdown(markdown)
        chain = self.core_prompt | self.core_llm.with_structured_output(
            CoreInfoSchema, 
            method="json_mode" 
        )
        return await chain.ainvoke({"markdown": safe_markdown})
    
    async def _extract_skills(self, markdown: str) -> SkillSetSchema:
        # Skills usually live in the first half of a JD anyway
        # 8,000 chars is plenty for tech stack/responsibilities
        safe_markdown = self._truncate_markdown(markdown, limit=8000)
        chain = self.skill_prompt | self.skill_llm.with_structured_output(
            SkillSetSchema, 
            method="json_mode"
        )
        return await chain.ainvoke({"markdown": safe_markdown})
    
    async def parse(self, markdown: str) -> JobExtraction:
        # 1. Extract Core Info
        print("🚀 Starting Core Extraction...")
        safe_markdown_core = self._truncate_markdown(markdown, self.MAX_CHARS)
        core_chain = self.core_prompt | self.core_llm.with_structured_output(
            CoreInfoSchema, 
            method="json_mode" 
        )
        core_res = await core_chain.ainvoke({"markdown": safe_markdown_core})

        # 2. Wait for 60 seconds to reset the Groq TPM bucket
        print("💤 Sleeping for 60s to respect Rate Limits...")
        await asyncio.sleep(60)

        # 3. Extract Skills
        print("🚀 Starting Skill Extraction...")
        # Even for skills, we can now afford a larger window
        safe_markdown_skills = self._truncate_markdown(markdown, self.MAX_CHARS)
        skill_chain = self.skill_prompt | self.skill_llm.with_structured_output(
            SkillSetSchema, 
            method="json_mode"
        )
        
        try:
            skill_res = await skill_chain.ainvoke({"markdown": safe_markdown_skills})
            skill_dict = skill_res.model_dump()
        except Exception as e:
            print(f"⚠️ Skill extraction failed: {e}")
            skill_dict = {"tech_stack": [], "soft_skills": [], "responsibilities": []}

        # 4. Merge and Return
        merged = {**core_res.model_dump(), **skill_dict}
        return JobExtraction.model_validate(merged)
# Usage in your loop:
# parser = JobParser()
# job_data = asyncio.run(parser.parse(raw_markdown))