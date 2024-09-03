from expr.nodes import Group
from pydantic import BaseModel


class RulesetCreate(BaseModel):
    name: str
    expression: Group
    is_active: bool


class RulesetEdit(BaseModel):
    name: str
    expression: Group
    is_active: bool
