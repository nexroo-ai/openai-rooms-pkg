<<<<<<< Updated upstream
from typing import Any, Optional, Dict, Generic, TypeVar
from pydantic import BaseModel, Field
=======
from pydantic import BaseModel
from typing import Optional

class TokensSchema(BaseModel):
    stepAmount: int
    totalCurrentAmount: int
>>>>>>> Stashed changes

class OutputBase(BaseModel):
    """Base pour les sorties d’actions."""
    pass

<<<<<<< Updated upstream
class TokensSchema(BaseModel):
    """Suivi token minimal utilisé par le script d’orchestration."""
    stepAmount: int = 0
    totalCurrentAmount: int = 0

T = TypeVar("T", bound=OutputBase)

class ActionResponse(Generic[T], BaseModel):
    """Envelope standard de réponse d’action."""
    output: T
=======
class ActionResponse(BaseModel):
    output: OutputBase
>>>>>>> Stashed changes
    tokens: TokensSchema
    message: str = "ok"
    code: int = 200
    meta: Optional[Dict[str, Any]] = None
