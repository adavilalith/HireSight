import asyncio
from typing import Dict, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from hiresight.processors.schemas import JobExtraction, CoreInfoSchema, SkillSetSchema

class JobParser:
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

    async def _extract_core(self, markdown: str) -> CoreInfoSchema:
        # Switch method to json_mode to bypass Groq's strict tool validator
        chain = self.core_prompt | self.core_llm.with_structured_output(
            CoreInfoSchema, 
            method="json_mode" 
        )
        return await chain.ainvoke({"markdown": markdown})

    async def _extract_skills(self, markdown: str) -> SkillSetSchema:
        # Same here for the 8B model
        chain = self.skill_prompt | self.skill_llm.with_structured_output(
            SkillSetSchema, 
            method="json_mode"
        )
        return await chain.ainvoke({"markdown": markdown[:6000]})

    async def parse(self, markdown: str) -> JobExtraction:
        async with self.bouncer:
            results = await asyncio.gather(
                self._extract_core(markdown),
                self._extract_skills(markdown),
                return_exceptions=True
            )
            
            # Error handling logic to prevent one failure from killing the pipeline
            core_res = results[0]
            skill_res = results[1]

            if isinstance(core_res, Exception):
                raise core_res # We need core info to proceed

            # Graceful degradation for skills
            if isinstance(skill_res, Exception):
                print(f"⚠️ Skill extraction failed: {skill_res}")
                skill_dict = {"tech_stack": [], "soft_skills": [], "responsibilities": []}
            else:
                skill_dict = skill_res.model_dump()

            merged = {**core_res.model_dump(), **skill_dict}
            return JobExtraction.model_validate(merged)
# Usage in your loop:
# parser = JobParser()
# job_data = asyncio.run(parser.parse(raw_markdown))