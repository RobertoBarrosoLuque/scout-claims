from modules.image_analysis import get_llm
from src.configs.load_config import PROMPT_LIBRARY, APP_STEPS_CONFIGS
from pydantic import BaseModel
from typing import Optional, Literal, List, Dict, Any
import json
import random
import time


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


class FunctionCallResult(BaseModel):
    function_name: str
    result: Dict[str, Any]
    status: Literal["success", "error"]
    message: str


class IncidentAnalysis(BaseModel):
    date_location: DateLocation
    parties_involved: PartiesInvolved
    fault_assessment: FaultAssessment
    incident_description: IncidentDescription
    injuries_medical: InjuriesMedical
    function_calls_made: List[FunctionCallResult] = []
    external_data_retrieved: Dict[str, Any] = {}


def mock_weather_lookup(date: str, location: str) -> Dict[str, Any]:
    """Mock function to look up weather conditions for a specific date and location"""
    time.sleep(0.5)  # Simulate API call delay

    weather_conditions = [
        "Clear",
        "Rainy",
        "Foggy",
        "Snowy",
        "Overcast",
        "Partly Cloudy",
    ]
    temperatures = range(20, 85)

    return {
        "date": date,
        "location": location,
        "temperature": f"{random.choice(temperatures)}°F",
        "conditions": random.choice(weather_conditions),
        "visibility": random.choice(["Good", "Poor", "Fair"]),
        "precipitation": random.choice(["None", "Light Rain", "Heavy Rain", "Snow"]),
        "wind_speed": f"{random.randint(0, 25)} mph",
    }


def mock_driver_record_check(
    driver_name: str, license_plate: str = None
) -> Dict[str, Any]:
    """Mock function to check driver record and vehicle registration"""
    risk_levels = ["Low", "Medium", "High"]

    return {
        "driver_found": True,
        "license_status": random.choice(["Valid", "Suspended", "Expired"]),
        "insurance_status": random.choice(["Active", "Lapsed", "Unknown"]),
        "previous_claims": random.randint(0, 5),
        "violations_last_3_years": random.randint(0, 3),
        "risk_assessment": random.choice(risk_levels),
        "vehicle_registration": "Valid" if license_plate else "Not checked",
    }


AVAILABLE_FUNCTIONS = {
    "weather_lookup": {
        "name": "weather_lookup",
        "description": "Look up weather conditions for a specific date and location to understand incident context",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Date of the incident"},
                "location": {
                    "type": "string",
                    "description": "Location where incident occurred",
                },
            },
            "required": ["date", "location"],
        },
        "function": mock_weather_lookup,
    },
    "driver_record_check": {
        "name": "driver_record_check",
        "description": "Check driving record and insurance status of other party involved",
        "parameters": {
            "type": "object",
            "properties": {
                "driver_name": {
                    "type": "string",
                    "description": "Name of the other driver",
                },
                "license_plate": {
                    "type": "string",
                    "description": "License plate number if available",
                },
            },
            "required": ["driver_name"],
        },
        "function": mock_driver_record_check,
    },
}


def execute_function_call(
    function_name: str, parameters: Dict[str, Any]
) -> FunctionCallResult:
    """Execute a function call and return the result"""
    try:
        if function_name not in AVAILABLE_FUNCTIONS:
            return FunctionCallResult(
                function_name=function_name,
                result={},
                status="error",
                message=f"Function {function_name} not found",
            )

        function_impl = AVAILABLE_FUNCTIONS[function_name]["function"]
        result = function_impl(**parameters)

        return FunctionCallResult(
            function_name=function_name,
            result=result,
            status="success",
            message=f"Successfully executed {function_name}",
        )

    except Exception as e:
        return FunctionCallResult(
            function_name=function_name,
            result={},
            status="error",
            message=f"Error executing {function_name}: {str(e)}",
        )


def process_transcript_description(transcript: str, api_key: str):
    """
    Analyze the provided transcript and extract structured information for insurance claim processing.
    Now includes function calling capabilities to gather additional context.

    Args:
        transcript: transcript string to process
        api_key: api key to use

    Returns:
        incident_description: incident description with function call results
    """
    print("Starting incident analysis with function calling...")

    llm = get_llm(
        api_key=api_key,
        model="accounts/fireworks/models/llama4-scout-instruct-basic",
        temperature=APP_STEPS_CONFIGS.incident_response.temperature,
    )

    # Enhanced prompt that includes function calling
    prompt_text = f"""
    {PROMPT_LIBRARY["incident_processing"]["advanced"]}

    **ADDITIONAL CAPABILITIES:**
    You now have access to external functions that can help gather additional context for the claim.
    Based on the transcript, you should consider calling these functions if the information would be helpful:

    Available Functions:
    {json.dumps([{k: {kk: vv for kk, vv in v.items() if kk != 'function'}} for k, v in AVAILABLE_FUNCTIONS.items()], indent=2)}

    **IMPORTANT:**
    1. First, extract all the basic incident information from the transcript
    2. Then determine which functions (if any) would provide helpful additional context
    3. For each function you want to call, include a "function_calls" section in your response
    4. I will execute the functions and provide you with the results
    5. You will then incorporate those results into your final analysis

    **TRANSCRIPT TO ANALYZE:**
    <transcript>
    {transcript}
    </transcript>

    Please provide your initial analysis and specify any function calls you'd like to make.
    """

    # First pass - get initial analysis and any function calls
    response = llm.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are an expert automotive claims adjuster analyzing vehicle damage with access to external data sources.",
            },
            {"role": "user", "content": prompt_text},
        ],
        response_format={
            "type": "json_object",
            "schema": IncidentAnalysis.model_json_schema(),
        },
        temperature=APP_STEPS_CONFIGS.incident_response.temperature,
    )

    # Parse initial response
    incident_data = IncidentAnalysis.model_validate_json(
        response.choices[0].message.content
    )

    print("Initial analysis complete. Checking for function calls...")

    function_calls_to_make = []
    external_data = {}

    if (
        incident_data.date_location.date
        and incident_data.date_location.location
        and incident_data.date_location.date.lower()
        not in ["not specified", "unknown", ""]
    ):
        function_calls_to_make.append(
            {
                "name": "weather_lookup",
                "params": {
                    "date": incident_data.date_location.date,
                    "location": incident_data.date_location.location,
                },
            }
        )

    if (
        incident_data.parties_involved.other_driver_name
        and incident_data.parties_involved.other_driver_name.lower()
        not in ["information not provided", "not specified", ""]
    ):
        function_calls_to_make.append(
            {
                "name": "driver_record_check",
                "params": {
                    "driver_name": incident_data.parties_involved.other_driver_name,
                    "license_plate": incident_data.parties_involved.other_driver_vehicle,
                },
            }
        )

    function_results = []
    if function_calls_to_make:
        print(f"Executing {len(function_calls_to_make)} function calls...")

        for call in function_calls_to_make:
            print(f"  - Calling {call['name']}...")
            result = execute_function_call(call["name"], call["params"])
            function_results.append(result)

            if result.status == "success":
                external_data[call["name"]] = result.result

    incident_data.function_calls_made = function_results
    incident_data.external_data_retrieved = external_data

    if function_results:
        print("Incorporating external data into final analysis...")

        enhancement_prompt = f"""
        Based on the initial incident analysis and the additional data retrieved from external sources,
        please provide an enhanced analysis that incorporates this new information.

        **INITIAL ANALYSIS:**
        {incident_data.model_dump_json(indent=2)}

        **EXTERNAL DATA RETRIEVED:**
        {json.dumps(external_data, indent=2)}

        Please update your analysis to incorporate insights from this external data where relevant.
        For example:
        - Weather conditions might affect fault assessment
        - Other traffic incidents might provide context
        - Driver record might influence risk assessment
        - Medical facility info might be relevant for injury cases

        Provide the complete updated analysis.
        """

        enhanced_response = llm.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert automotive claims adjuster incorporating external data into your analysis.",
                },
                {"role": "user", "content": enhancement_prompt},
            ],
            response_format={
                "type": "json_object",
                "schema": IncidentAnalysis.model_json_schema(),
            },
            temperature=APP_STEPS_CONFIGS.incident_response.temperature,
        )

        enhanced_data = IncidentAnalysis.model_validate_json(
            enhanced_response.choices[0].message.content
        )

        enhanced_data.function_calls_made = function_results
        enhanced_data.external_data_retrieved = external_data
        incident_data = enhanced_data

    print("Finished incident analysis with function calling.")
    return incident_data
