from typing import List, Optional, Any
from typing_extensions import Annotated
from pydantic import BaseModel, Field, BeforeValidator

# --- Helper Functions for Data Cleaning ---

def coerce_to_int(v: Any) -> Optional[int]:
    """Cleans '15,000', '15 LPA', and 'null' strings into actual integers."""
    if v is None or str(v).lower() in ("null", "none", "", "n/a"):
        return None
    if isinstance(v, (int, float)):
        return int(v)
    if isinstance(v, str):
        # Remove commas and handle 'LPA' for Indian context
        clean_v = v.replace(",", "").lower()
        if "lpa" in clean_v:
            # "15 LPA" -> 15 * 100,000
            try:
                num = float(clean_v.split("lpa")[0].strip())
                return int(num * 100_000)
            except ValueError:
                return None
        # Extract only digits (handles "$70,000" -> 70000)
        digits = "".join(filter(str.isdigit, clean_v))
        return int(digits) if digits else None
    return None

def coerce_to_bool(v: Any) -> bool:
    """Converts 'Yes', 'Remote', '1' or 'true' into a proper Boolean."""
    if isinstance(v, bool):
        return v
    if str(v).lower() in ("yes", "true", "1", "remote", "wfh"):
        return True
    return False

# --- Pydantic Models ---

class JobExtraction(BaseModel):
    # Categorical fields (Dashboard Filters)
    role: str = Field(description="Normalized job title")
    job_type: str = Field(description="Full-time, Part-time, or Contract")
    seniority: str = Field(description="Junior, Mid, Senior, or Lead")
    
    # Cleaned Boolean
    is_remote: Annotated[bool, BeforeValidator(coerce_to_bool)] = Field(
        default=False, description="Explicit remote/WFH mention"
    )
    
    # Cleaned Integers for Salary Trends
    salary_min: Annotated[Optional[int], BeforeValidator(coerce_to_int)] = None
    salary_max: Annotated[Optional[int], BeforeValidator(coerce_to_int)] = None
    salary_currency: str = Field(default="INR", description="ISO Currency code")
    
    # List fields (Heatmaps / Deep Dives)
    tech_stack: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    
    education_required: Optional[str] = Field(None, description="Bachelors, Masters, etc.")



class CoreInfoSchema(BaseModel):
    role: str
    job_type: str
    seniority: str
    is_remote: Annotated[bool, BeforeValidator(coerce_to_bool)]
    salary_min: Annotated[Optional[int], BeforeValidator(coerce_to_int)]
    salary_max: Annotated[Optional[int], BeforeValidator(coerce_to_int)]
    salary_currency: str = "INR"
    education_required: Optional[str] = None

class SkillSetSchema(BaseModel):
    tech_stack: List[str]
    soft_skills: List[str]
    responsibilities: List[str]