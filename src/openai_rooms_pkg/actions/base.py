from typing import Any, Optional, Dict, Generic, TypeVar
from pydantic import BaseModel, Field

class OutputBase(BaseModel):
    """Base pour les sorties d’actions."""
    pass

class TokensSchema(BaseModel):
    """Suivi token minimal utilisé par le script d’orchestration."""
    stepAmount: int = 0
    totalCurrentAmount: int = 0

T = TypeVar("T", bound=OutputBase)

class ActionResponse(Generic[T], BaseModel):
    """Envelope standard de réponse d’action."""
    output: T
    tokens: TokensSchema
    message: str = "ok"
    code: int = 200
    meta: Optional[Dict[str, Any]] = None
