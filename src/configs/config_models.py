from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    model: str
    temperature: float = Field(default=0.1, ge=0, le=1.0)


class StepModelsConfigs(BaseModel):
    analyze_damage_image: ModelConfig
    incident_response: ModelConfig
    report_generation: ModelConfig
