# FILE: src/openai_rooms_pkg/base.py
from typing import Optional
from pydantic import BaseModel


class TokensSchema(BaseModel):
    stepAmount: int
    totalCurrentAmount: int


class OutputBase(BaseModel):
    pass


class ActionResponse(BaseModel):
    output: OutputBase
    tokens: TokensSchema
    message: Optional[str]
    code: Optional[int]
