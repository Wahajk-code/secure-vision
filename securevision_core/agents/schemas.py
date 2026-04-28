from pydantic import BaseModel, Field


class TriageOutput(BaseModel):
    dashboard_title: str = Field(..., description="Short dashboard card title for the alert.")
    operator_summary: str = Field(..., description="Brief operator-facing summary of what is happening.")
    risk_explanation: str = Field(..., description="Why the system considers the alert risky right now.")
    recommended_priority: str = Field(..., description="Operational priority label such as IMMEDIATE, HIGH, or STANDARD.")
    tts_message: str = Field(..., description="Short spoken alert text grounded in the incident context.")
    requires_operator_review: bool = Field(..., description="Whether the alert should remain visible for operator review.")


class TimelineOutput(BaseModel):
    incident_title: str = Field(..., description="Stable title for the grouped incident.")
    timeline_summary: str = Field(..., description="Brief summary of how the incident is evolving over time.")
    recommended_next_step: str = Field(..., description="Short next action recommendation grounded in incident continuity.")


class ActionsOutput(BaseModel):
    action_plan: list[str] = Field(..., description="Ordered list of operator steps to take next.")
    operator_note: str = Field(..., description="Brief contextual note for the operator.")
    escalation_hint: str = Field(..., description="Condition-based escalation guidance.")
