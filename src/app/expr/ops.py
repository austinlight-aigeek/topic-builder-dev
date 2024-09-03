from enum import StrEnum

from pydantic import BaseModel


class QBType(StrEnum):
    STRING = "string"
    NUMBER = "number"
    DATETIME = "datetime"
    BOOLEAN = "boolean"


# jQuery QueryBuilder custom operator specification
class QBOperatorSpec(BaseModel):
    apply_to: list[QBType]
    nb_inputs: int
    multiple: bool = False
    type: str


# Conditions for Groups
class Condition(StrEnum):
    AND = "AND"
    OR = "OR"


# Base class for Operator.
# Other Operator classes should reference the values in this enum.
# The SQL generator should support all operators in this enum.
class Operator(StrEnum):
    IN = "in"
    NOT_IN = "not_in"
    GREATER = "greater"
    LESS = "less"
    MATCH = "match"
    NOT_MATCH = "not_match"
    AFTER = "after"
    BEFORE = "before"


CUSTOM_OPERATORS: dict[Operator, QBOperatorSpec] = {
    Operator.MATCH: QBOperatorSpec(apply_to=["string"], nb_inputs=1, type=Operator.MATCH.value),
    Operator.NOT_MATCH: QBOperatorSpec(apply_to=["string"], nb_inputs=1, type=Operator.NOT_MATCH.value),
    Operator.AFTER: QBOperatorSpec(apply_to=["datetime"], nb_inputs=1, type=Operator.AFTER.value),
    Operator.BEFORE: QBOperatorSpec(apply_to=["datetime"], nb_inputs=1, type=Operator.BEFORE.value),
}


class SourceOperator(StrEnum):
    IN = Operator.IN
    NOT_IN = Operator.NOT_IN


class SentimentOperator(StrEnum):
    IN = Operator.IN
    NOT_IN = Operator.NOT_IN


class IntentOperator(StrEnum):
    IN = Operator.IN
    NOT_IN = Operator.NOT_IN


class LemmaOperator(StrEnum):
    IN = Operator.IN
    NOT_IN = Operator.NOT_IN


class SimilarityOperator(StrEnum):
    GREATER = Operator.GREATER
    LESS = Operator.LESS


class RegexOperator(StrEnum):
    MATCH = Operator.MATCH
    NOT_MATCH = Operator.NOT_MATCH


class DateOperator(StrEnum):
    AFTER = Operator.AFTER
    BEFORE = Operator.BEFORE
