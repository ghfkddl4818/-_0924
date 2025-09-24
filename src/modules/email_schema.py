"""Schema definitions for cold email generation outputs."""

from __future__ import annotations

from typing import Iterable, List

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

REQUIRED_EMAIL_META_KEYS = ("product_name", "unique_features", "call_to_action")


class ColdEmailMeta(BaseModel):
    """Structured representation of the metadata block expected from the LLM."""

    model_config = ConfigDict(extra="forbid")

    product_name: str = Field(..., min_length=1)
    unique_features: List[str]
    call_to_action: str = Field(..., min_length=1)

    @field_validator("product_name", "call_to_action", mode="before")
    @classmethod
    def _strip_string(cls, value: str) -> str:
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                raise ValueError("값은 비어 있을 수 없습니다")
            return stripped
        raise TypeError("문자열 값이어야 합니다")

    @field_validator("unique_features", mode="before")
    @classmethod
    def _normalise_features(cls, value: object) -> List[str]:
        if isinstance(value, str):
            items: Iterable[str] = value.splitlines() or [value]
        elif isinstance(value, Iterable):
            items = [str(item) for item in value]
        else:  # pragma: no cover - defensive branch
            raise TypeError("unique_features는 문자열 또는 문자열 목록이어야 합니다")

        normalised = [item.strip() for item in items if str(item).strip()]
        if not normalised:
            raise ValueError("unique_features는 최소 1개 이상의 항목이 필요합니다")
        return normalised

    @model_validator(mode="after")
    def _ensure_unique_features(self) -> "ColdEmailMeta":
        if not self.unique_features:
            raise ValueError("unique_features는 비어 있을 수 없습니다")
        return self


__all__ = ["ColdEmailMeta", "REQUIRED_EMAIL_META_KEYS"]
