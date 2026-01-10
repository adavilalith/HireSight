import pytest
import os
from hiresight.processors.job_parser import JobParser

@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_llm_extraction():
    """Smoke test to ensure Groq returns valid JSON that maps to our Pydantic models."""
    if not os.getenv("GROQ_API_KEY"):
        pytest.skip("GROQ_API_KEY not found in environment")
        
    parser = JobParser()
    sample_markdown = """
    We are looking for a Senior Data Scientist. 
    Pay is 25,00,000 to 35,00,000 INR per year. 
    Fully remote. Must know Python, PyTorch, and SQL. 
    You will build ML models and mentor juniors.
    """
    
    result = await parser.parse(sample_markdown)
    
    # Assertions to verify LLM logic
    assert "Scientist" in result.role
    assert result.is_remote is True
    assert result.salary_min >= 2500000
    assert "Python" in [s.capitalize() for s in result.tech_stack]
    assert len(result.responsibilities) > 0