import pytest
from unittest.mock import AsyncMock, patch
from hiresight.processors.job_parser import JobParser
from hiresight.processors.schemas import CoreInfoSchema, SkillSetSchema, JobExtraction

@pytest.mark.unit
@pytest.mark.asyncio
async def test_parse_successful_merge():
    """Test that core and skill data are merged correctly into JobExtraction."""
    parser = JobParser()
    
    # Create sample return objects
    mock_core = CoreInfoSchema(
        role="Data Engineer", job_type="Full-time", seniority="Senior",
        is_remote=True, salary_min=1500000, salary_max=2000000,
        salary_currency="INR", education_required="Bachelors"
    )
    mock_skills = SkillSetSchema(
        tech_stack=["Python", "SQL"], soft_skills=["Communication"], 
        responsibilities=["Data Pipeline Build"]
    )

    # Patch the internal extraction methods
    with patch.object(parser, '_extract_core', new_callable=AsyncMock) as mock_c, \
         patch.object(parser, '_extract_skills', new_callable=AsyncMock) as mock_s:
        
        mock_c.return_value = mock_core
        mock_s.return_value = mock_skills
        
        result = await parser.parse("fake markdown content")
        
        assert isinstance(result, JobExtraction)
        assert result.role == "Data Engineer"
        assert "Python" in result.tech_stack
        assert result.is_remote is True

@pytest.mark.unit
@pytest.mark.asyncio
async def test_parse_graceful_degradation_on_skill_failure():
    """Test that if skills extraction fails, we still get core data with empty lists."""
    parser = JobParser()
    
    mock_core = CoreInfoSchema(
        role="Analyst", job_type="Contract", seniority="Mid",
        is_remote=False, salary_min=None, salary_max=None,
        salary_currency="INR", education_required=None
    )

    with patch.object(parser, '_extract_core', new_callable=AsyncMock) as mock_c, \
         patch.object(parser, '_extract_skills', new_callable=AsyncMock) as mock_s:
        
        mock_c.return_value = mock_core
        # Simulate an LLM timeout or validation error
        mock_s.side_effect = Exception("Groq Overloaded")
        
        result = await parser.parse("fake markdown content")
        
        assert result.role == "Analyst"
        assert result.tech_stack == [] # Successfully degraded
        assert result.responsibilities == []