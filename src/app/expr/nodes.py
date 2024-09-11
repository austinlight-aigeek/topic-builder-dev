import json
from datetime import date
from enum import StrEnum
from typing import Annotated, Literal

from expr.ops import (
    Condition,
    DateOperator,
    IntentOperator,
    LemmaOperator,
    RegexOperator,
    SentimentOperator,
    SimilarityOperator,
    SourceOperator,
)
from pydantic import (
    BaseModel,
    Field,
    SerializeAsAny,
    field_serializer,
    model_serializer,
    model_validator,
)
from util import enum_to_list


class ExprNode(BaseModel):
    pass


class Rule(ExprNode):
    def to_filter():
        raise NotImplementedError


class Group(ExprNode):
    # Frontend does not provide an id.
    # Add it before Pydantic validation sees it.
    @model_validator(mode="before")
    @staticmethod
    def validate(data):
        if isinstance(data, dict) and "id" not in data:
            data["id"] = "Group"
        return data

    id: Literal["Group"] = "Group"
    condition: Condition
    not_: bool = Field(..., alias="not")
    rules: list[SerializeAsAny["AnyExprNode"]] = []


class SourceValue(StrEnum):
    MENTOR = "mentor note"
    ENROLLMENT = "enrollment note"
    EMAIL = "email"


class Source(Rule):
    id: Literal["Source"] = "Source"
    operator: SourceOperator = SourceOperator.IN
    value: list[SourceValue] = enum_to_list(SourceValue)

    def to_filter():
        return {
            "id": "Source",
            "label": "Source",
            "values": enum_to_list(SourceValue),
            "operators": enum_to_list(SourceOperator),
            "description": "NLP sources to search in.",
            "type": "string",
            "input": "checkbox",
            "color": "primary",
        }


class SentimentValue(StrEnum):
    VERY_NEGATIVE = "very negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very positive"


class Sentiment(Rule):
    id: Literal["Sentiment"] = "Sentiment"
    operator: SentimentOperator = SentimentOperator.IN
    value: list[SentimentValue] = enum_to_list(SentimentValue)

    def to_filter():
        return {
            "id": "Sentiment",
            "label": "Sentiment",
            "values": enum_to_list(SentimentValue),
            "operators": enum_to_list(SentimentOperator),
            "description": "Sentiment of the sentence.",
            "type": "string",
            "input": "checkbox",
            "color": "primary",
        }


class IntentValue(StrEnum):
    ACTION_REQUEST = "action-request"
    REQUEST = "request"
    YES_NO_QUESTION = "yes-no-question"
    STATEMENT = "statement"
    INFORMATION_REQUEST = "information-request"


class Intent(Rule):
    id: Literal["Intent"] = "Intent"
    operator: IntentOperator = IntentOperator.IN
    value: list[IntentValue] = enum_to_list(IntentValue)

    def to_filter():
        return {
            "id": "Intent",
            "label": "Intent",
            "values": enum_to_list(IntentValue),
            "operators": enum_to_list(IntentOperator),
            "description": "Intent of the sentence.",
            "type": "string",
            "input": "checkbox",
            "color": "primary",
        }


class Lemma(Rule):
    id: Literal["Lemma"] = "Lemma"
    operator: LemmaOperator = LemmaOperator.IN
    value: str = ""

    def to_filter():
        return {
            "id": "Lemma",
            "label": "Lemma",
            "operators": enum_to_list(LemmaOperator),
            "description": "Lemmatized word matching.",
            "type": "string",
        }


class Similarity(Rule):
    id: Literal["Similarity"] = "Similarity"
    operator: SimilarityOperator = SimilarityOperator.GREATER
    text: str = ""
    threshold: float = Field(ge=-1, le=1)

    def to_filter():
        return {
            "id": "Similarity",
            "label": "Similarity",
            "operators": enum_to_list(SimilarityOperator),
            "description": "Sentence similarity based on embeddings (-1 to 1.) Sensitivity can be controlled with the threshold slider.",
            "type": "string",
            # These JS functions are hydrated in the frontend
            "input": None,
            "valueGetter": None,
            "valueSetter": None,
        }

    # Frontend sends back value and threshold packaged as a JSON string.
    # Unpackage JSON string "value" before Pydantic validation sees it.
    @model_validator(mode="before")
    @staticmethod
    def validate(data):
        if "id" not in data or data["id"] != "Similarity":
            return {}
        if "value" in data:
            data = {**data, **json.loads(data["value"])}
            del data["value"]
        return data

    # When serializing for the frontend, package value and threshold as a JSON string.
    @model_serializer(when_used="json")
    def json_serialize(self):
        return {
            "id": self.id,
            "operator": str(self.operator),
            "value": json.dumps({"text": self.text, "threshold": self.threshold}),
        }


class Regex(Rule):
    id: Literal["Regex"] = "Regex"
    operator: RegexOperator = RegexOperator.MATCH
    value: str = ""

    def to_filter():
        return {
            "id": "Regex",
            "label": "Regex",
            "operators": enum_to_list(RegexOperator),
            "description": "Regular expression matching.",
            "type": "string",
        }


class Date(Rule):
    id: Literal["Date"] = "Date"
    operator: DateOperator = DateOperator.AFTER
    value: date

    @field_serializer("value")
    def serialize_value(self, value: date):
        return value.isoformat()

    def to_filter():
        return {
            "id": "Date",
            "label": "Date",
            "operators": enum_to_list(DateOperator),
            "description": "Date-based filtering.",
            "type": "datetime",
            "plugin": "datepicker",
            "plugin_config": {
                "format": "yyyy-mm-dd",
                "todayBtn": "linked",
                "autoclose": True,
            },
        }


# Discriminated union to determine model
# Need to treat Groups differently as query builder does not provide an id for that one
AnyExprNode = (
    Group
    | Annotated[
        Source | Sentiment | Intent | Lemma | Similarity | Regex | Date,
        Field(discriminator="id"),
    ]
)
