import pytest

from app.agents.fraud_risk.runner import FraudRiskAgentRunner
from app.core.errors import AppError


def test_fraud_agent_validator_accepts_supported_risk_statuses():
    assert FraudRiskAgentRunner._validated_risk_status("low_risk") == "low_risk"
    assert FraudRiskAgentRunner._validated_risk_status("medium_risk") == "medium_risk"
    assert FraudRiskAgentRunner._validated_risk_status("high_risk") == "high_risk"


def test_fraud_agent_validator_rejects_unknown_status():
    with pytest.raises(AppError) as exc_info:
        FraudRiskAgentRunner._validated_risk_status("critical")

    assert exc_info.value.code == "validation_error"
