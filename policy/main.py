from typing import Any

from agent_os.policies import (
    PolicyAction,
    PolicyCondition,
    PolicyDefaults,
    PolicyDocument,
    PolicyEvaluator,
    PolicyOperator,
    PolicyRule,
)
from fastapi import FastAPI
from pydantic import BaseModel

POLICY_NAME = "weather-agent-tool-policy"
SUSPICIOUS_LOCATION_PATTERN = (
    r"(?i)(ignore|system prompt|secret|token|password|delete|execute|rm -rf|drop table)"
)


class EvaluateActionRequest(BaseModel):
    tool_name: str
    location: str


evaluator = PolicyEvaluator(
    policies=[
        PolicyDocument(
            name=POLICY_NAME,
            version="1.0",
            defaults=PolicyDefaults(action=PolicyAction.DENY),
            rules=[
                PolicyRule(
                    name="block-unknown-tool",
                    condition=PolicyCondition(
                        field="tool_name",
                        operator=PolicyOperator.NE,
                        value="get_weather",
                    ),
                    action=PolicyAction.DENY,
                    priority=400,
                ),
                PolicyRule(
                    name="block-empty-input",
                    condition=PolicyCondition(
                        field="location",
                        operator=PolicyOperator.MATCHES,
                        value=r"^\s*$",
                    ),
                    action=PolicyAction.DENY,
                    priority=300,
                ),
                PolicyRule(
                    name="block-suspicious-input",
                    condition=PolicyCondition(
                        field="location",
                        operator=PolicyOperator.MATCHES,
                        value=SUSPICIOUS_LOCATION_PATTERN,
                    ),
                    action=PolicyAction.DENY,
                    priority=200,
                ),
                PolicyRule(
                    name="allow-weather-tool",
                    condition=PolicyCondition(
                        field="tool_name",
                        operator=PolicyOperator.EQ,
                        value="get_weather",
                    ),
                    action=PolicyAction.ALLOW,
                    priority=100,
                ),
            ],
        ),
    ]
)

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Running!"}


@app.get("/health")
def health_check():
    return {"status": "policy server healthy"}


@app.get("/policy")
def get_policy():
    return {
        "name": POLICY_NAME,
        "default_action": "deny",
        "allowed_tools": ["get_weather"],
        "blocked_location_patterns": SUSPICIOUS_LOCATION_PATTERN,
    }


@app.post("/evaluate-action")
def evaluate_action(request: EvaluateActionRequest):
    location = request.location
    decision = evaluator.evaluate(
        {
            "tool_name": request.tool_name,
            "location": location,
        }
    )

    return {
        "allowed": decision.allowed,
        "reason": decision.reason,
        "matched_rule": decision.matched_rule,
        "policy": POLICY_NAME,
        "audit": decision.audit_entry,
    }
