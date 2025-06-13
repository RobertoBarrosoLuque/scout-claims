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
    witnesses: Optional[str] = None


class FaultAssessment(BaseModel):
    who_at_fault: Literal["me", "other_driver", "unclear"]
    reason: str


class IncidentDescription(BaseModel):
    what_happened: str
    damage_severity: Literal["minor", "moderate", "severe", "unclear"]


class InjuriesMedical(BaseModel):
    anyone_injured: Literal["yes", "no", "unknown"]
    injury_details: Optional[str] = None
    medical_attention: Optional[str] = None
    injury_severity: Optional[Literal["none", "minor", "moderate", "severe", "unclear"]]


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
    print("Starting incident analysis...")
    llm = get_llm(
        api_key=api_key,
        model="accounts/fireworks/models/llama4-scout-instruct-basic",
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
                "content": "You are an expert automotive claims adjuster analyzing vehicle damage.",
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
    print("Finished incident analysis.")
    return incident_data
