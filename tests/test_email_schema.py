from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.modules.email_schema import ColdEmailMeta


def test_cold_email_meta_accepts_valid_payload() -> None:
    payload = {
        "product_name": "Ultimate Battery Pack",
        "unique_features": ["10시간 초고속 충전", "모듈형 확장"],
        "call_to_action": "데모 미팅 일정을 논의하고 싶습니다.",
    }

    meta = ColdEmailMeta.model_validate(payload)

    assert meta.product_name == "Ultimate Battery Pack"
    assert meta.unique_features == ["10시간 초고속 충전", "모듈형 확장"]
    assert meta.call_to_action == "데모 미팅 일정을 논의하고 싶습니다."


def test_cold_email_meta_rejects_missing_required_key() -> None:
    with pytest.raises(ValidationError):
        ColdEmailMeta.model_validate(
            {
                "product_name": "Ultimate Battery Pack",
                "unique_features": "10시간 초고속 충전",
            }
        )
