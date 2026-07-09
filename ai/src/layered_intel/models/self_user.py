from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class SelfModel(BaseModel):
    identity_name: str = Field(default="Assistant", max_length=120)
    core_values: list[str] = Field(default_factory=list)
    boundaries: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    limits: list[str] = Field(default_factory=list)
    ongoing_projects: list[str] = Field(default_factory=list)
    behavior_notes: str = Field(default="", max_length=4000)

    @field_validator("core_values", "boundaries", "strengths", "limits", "ongoing_projects")
    @classmethod
    def _cap_list(cls, v: list[str]) -> list[str]:
        return [str(x)[:500] for x in v[:50]]


class UserModel(BaseModel):
    preferred_name: str | None = Field(default=None, max_length=120)
    communication_style: str | None = Field(default=None, max_length=500)
    stated_goals: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    facts: list[str] = Field(default_factory=list)

    @field_validator("stated_goals", "open_questions", "facts")
    @classmethod
    def _cap_list(cls, v: list[str]) -> list[str]:
        return [str(x)[:800] for x in v[:80]]


def merge_self(base: SelfModel, patch: dict[str, Any]) -> SelfModel:
    data = base.model_dump()
    allowed = set(SelfModel.model_fields)
    for k, v in patch.items():
        if k in allowed:
            data[k] = v
    return SelfModel.model_validate(data)


def merge_user(base: UserModel, patch: dict[str, Any]) -> UserModel:
    data = base.model_dump()
    allowed = set(UserModel.model_fields)
    for k, v in patch.items():
        if k in allowed:
            data[k] = v
    return UserModel.model_validate(data)
