from modules.image_analysis import get_llm
from src.configs.load_config import PROMPT_LIBRARY, APP_STEPS_CONFIGS
from pydantic import BaseModel
from typing import Optional, Literal


class DateLocation(BaseModel):
    date: Optional[str] = None
    time: Optional[str] = None
    location: Optional[str] = None


class PartiesInvolved(BaseModel):
    other_driver_name: Optional[str] = None
    other_driver_vehicle: Optional[str] = None
    other_driver_contact_or_insurance: Optional[str] = None
    witnesses: Optional[str] = None


class FaultAssessment(BaseModel):
    who_at_fault: Optional[Literal["me", "other_driver", "both", "unclear"]] = None
    reason: Optional[str] = None


class IncidentDescription(BaseModel):
    what_happened: Optional[str] = None
    damage_severity: Optional[Literal["minor", "moderate", "severe"]] = None


class InjuriesMedical(BaseModel):
    anyone_injured: Optional[Literal["yes", "no", "unknown"]] = None
    injury_details: Optional[str] = None
    medical_attention: Optional[Literal["none", "scene", "hospital", "ongoing"]] = None
    injury_severity: Optional[Literal["none", "minor", "moderate", "severe"]] = None


class IncidentAnalysis(BaseModel):
    date_location: DateLocation
    parties_involved: PartiesInvolved
    fault_assessment: FaultAssessment
    incident_description: IncidentDescription
    injuries_medical: InjuriesMedical


def process_transcript_description(transcript: str, api_key: str):
    """
    Analyze the provided transcript and extract structured information for insurance claim processing.

    Args:
        transcript: transcript string to process
        api_key: api key to use

    Returns:
        incident_description: incident description
    """
    llm = get_llm(
        api_key=api_key,
        model=APP_STEPS_CONFIGS.incident_response.model,
        temperature=APP_STEPS_CONFIGS.incident_response.temperature,
    )

    prompt_text = PROMPT_LIBRARY["incident_processing"]["advanced"]

    full_prompt = f"""
    {prompt_text}

    **TRANSCRIPT TO ANALYZE:**
    <transcript>
    {transcript}
    </transcript>
    """

    response = llm.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are an expert automotive claims adjuster. "
                "Analyze the provided transcript and extract structured information for "
                "insurance claim processing.",
            },
            {"role": "user", "content": full_prompt},
        ],
        response_format={
            "type": "json_object",
            "schema": IncidentAnalysis.model_json_schema(),
        },
        temperature=APP_STEPS_CONFIGS.incident_response.temperature,
    )

    incident_data = IncidentAnalysis.model_validate_json(
        response.choices[0].message.content
    )

    return incident_data
